"""
cast_ko 잔여 외국어 이름 → 한글 음역 변환 스크립트

대상: 영어, 중국어(한자), 일본어(가나), 악센트 라틴, 그리스어 등 모든 비한글 이름
방식: Claude API 배치 처리 (50개/배치)
저장: 배치별 즉시 DB 저장 + JSON 진행 파일로 중단/재개 지원

사용법:
  cd backend
  ./venv/Scripts/python.exe scripts/transliterate_foreign_names.py           # 실행
  ./venv/Scripts/python.exe scripts/transliterate_foreign_names.py --dry-run # 영향 범위만 확인
  ./venv/Scripts/python.exe scripts/transliterate_foreign_names.py --no-resume  # 처음부터

진행 파일: backend/scripts/foreign_transliteration_progress.json
"""
import os, sys, json, time, io, re, argparse, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
MODEL = "claude-sonnet-4-20250514"
BATCH_SIZE = 50
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "foreign_transliteration_progress.json")


# ===== 1. 외국어 이름 추출 =====

def is_fully_korean(name):
    """이름이 완전히 한글(+숫자/공백/일반기호)인지 판별"""
    for ch in name:
        cp = ord(ch)
        # 한글 (가-힣, ㄱ-ㅎ, ㅏ-ㅣ)
        if 0xAC00 <= cp <= 0xD7AF or 0x3131 <= cp <= 0x318E:
            continue
        # 숫자, 공백, 일반 기호
        if ch in ' \t·.,-()\'"/&!?#@:;0123456789':
            continue
        # 여기 도달하면 외국 문자
        return False
    return True


def classify_name(name):
    """이름의 스크립트 분류"""
    has_cjk = False
    has_kana = False
    has_latin = False
    has_accented = False
    has_greek = False
    has_cyrillic = False
    has_other = False

    for ch in name:
        cp = ord(ch)
        cat = unicodedata.category(ch)
        # 한글은 무시
        if 0xAC00 <= cp <= 0xD7AF or 0x3131 <= cp <= 0x318E:
            continue
        if ch in ' \t·.,-()\'"/&!?#@:;0123456789':
            continue
        # CJK 한자
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF:
            has_cjk = True
        # 히라가나/카타카나
        elif 0x3040 <= cp <= 0x30FF or 0x31F0 <= cp <= 0x31FF or 0xFF65 <= cp <= 0xFF9F:
            has_kana = True
        # 기본 라틴
        elif 0x0041 <= cp <= 0x007A:
            has_latin = True
        # 그리스어
        elif 0x0370 <= cp <= 0x03FF or 0x1F00 <= cp <= 0x1FFF:
            has_greek = True
        # 키릴
        elif 0x0400 <= cp <= 0x04FF:
            has_cyrillic = True
        # 확장 라틴 (악센트)
        elif cat.startswith('L') and cp > 127:
            has_accented = True
        # 기타 (태국어, 아랍어, 데바나가리 등)
        elif cat.startswith('L') or cat.startswith('M'):
            has_other = True

    if has_kana:
        return 'japanese'
    if has_cjk:
        return 'chinese'
    if has_greek:
        return 'greek'
    if has_cyrillic:
        return 'cyrillic'
    if has_accented and not has_latin:
        return 'accented'
    if has_accented and has_latin:
        return 'accented_latin'
    if has_latin:
        return 'english'
    if has_other:
        return 'other'
    return None


def extract_foreign_names(conn):
    """DB에서 cast_ko의 비한글 이름과 등장 빈도 추출"""
    cur = conn.cursor()
    cur.execute("SELECT id, cast_ko FROM movies WHERE cast_ko IS NOT NULL AND cast_ko != ''")

    name_freq = {}
    name_type = {}
    for movie_id, cast_ko in cur.fetchall():
        names = [n.strip() for n in cast_ko.split(',')]
        for name in names:
            if not name:
                continue
            if is_fully_korean(name):
                continue
            # 비한글 문자가 포함된 이름
            name_freq[name] = name_freq.get(name, 0) + 1
            if name not in name_type:
                name_type[name] = classify_name(name)

    return name_freq, name_type


# ===== 2. 진행 상태 관리 =====

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data.setdefault("translated", {})
            data.setdefault("failed_batches", [])
            data.setdefault("total_input_tokens", 0)
            data.setdefault("total_output_tokens", 0)
            return data
    return {
        "translated": {},
        "failed_batches": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }


def save_progress(progress):
    tmp_file = PROGRESS_FILE + ".tmp"
    try:
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        os.rename(tmp_file, PROGRESS_FILE)
    except OSError as e:
        print(f"    [WARN] 진행 파일 저장 실패: {e} (DB는 정상 반영됨)")
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass


# ===== 3. Claude API 음역 변환 =====

def transliterate_batch(names, retry=0):
    names_text = "\n".join(f"{i+1}. {name}" for i, name in enumerate(names))

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system="""You are an expert transliterator. Convert foreign names to Korean (한글) phonetic transliteration.

RULES:

1. Chinese characters (한자) → Korean reading based on original Chinese/Japanese pronunciation
   "周星馳" → "저우싱치"
   "張國榮" → "장궈룽"
   "劉德華" → "류더화"
   "成龍" → "청룽"
   "梁朝偉" → "량차오웨이"
   "鞏俐" → "궁리"
   If the name appears to be Japanese (mixed with kana or Japanese-style), use Japanese pronunciation:
   "宮崎駿" → "미야자키 하야오"
   "三船敏郎" → "미후네 도시로"

2. Japanese (hiragana/katakana) → Korean based on Japanese pronunciation
   "きたろう" → "기타로"
   "きゃりーぱみゅぱみゅ" → "캬리 파뮤파뮤"
   "たけし" → "다케시"

3. Greek alphabet → Korean based on Greek pronunciation
   "Αλέξης Γεωργούλης" → "알렉시스 게오르굴리스"
   "Μάκης Παπαδημητρίου" → "마키스 파파디미트리우"

4. Cyrillic → Korean based on original pronunciation
   "Владимир" → "블라디미르"

5. Accented Latin → Korean reflecting original pronunciation
   "Éric Elmosnino" → "에릭 엘모스니노"
   "Javier Bardem" → "하비에르 바르뎀"
   "Gérard Depardieu" → "제라르 드파르디외"
   "Horăţiu Mălăele" → "호라치우 멀러엘레"

6. English names → Korean
   "Bruce Willis" → "브루스 윌리스"
   "Katie O'Grady" → "케이티 오그레이디"

7. Names with "및" (meaning "and") → transliterate each part
   "Alessandro Calabrese 및 Andrea Vergoni" → "알레산드로 칼라브레세 및 안드레아 베르고니"

8. Initials (A.J., DJ, MC etc.) → keep as-is, transliterate the rest
   "AJ 보웬" → keep as-is (already has Korean)
   "DJ Qualls" → "DJ 퀄스"

9. Mixed Korean+foreign → only transliterate the foreign parts
   If already mostly Korean with just initials like "AJ 보웬", return as-is.

Return ONLY valid JSON: {"original_name": "한글음역", ...}
No explanation, no markdown, just pure JSON.""",
            messages=[{
                "role": "user",
                "content": f"Convert these {len(names)} names to Korean transliteration:\n\n{names_text}"
            }]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)

        translations = {}
        for name in names:
            if name in result:
                kor = result[name].strip()
                if re.search(r'[가-힣]', kor):
                    translations[name] = kor
                else:
                    translations[name] = name
            else:
                translations[name] = name

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        return translations, input_tokens, output_tokens

    except json.JSONDecodeError as e:
        if retry < 2:
            print(f"    JSON 파싱 실패, 재시도 ({retry+1}/2)...")
            time.sleep(2)
            return transliterate_batch(names, retry + 1)
        print(f"    JSON 파싱 최종 실패: {e}")
        return {}, 0, 0

    except anthropic.RateLimitError:
        wait = 30 * (retry + 1)
        print(f"    Rate limit, {wait}초 대기...")
        time.sleep(wait)
        if retry < 3:
            return transliterate_batch(names, retry + 1)
        return {}, 0, 0

    except Exception as e:
        if retry < 2:
            print(f"    에러: {e}, 재시도 ({retry+1}/2)...")
            time.sleep(3)
            return transliterate_batch(names, retry + 1)
        print(f"    최종 에러: {e}")
        return {}, 0, 0


# ===== 4. DB 업데이트 =====

def update_db_with_translations(conn, translations):
    cur = conn.cursor()
    total_updated = 0

    for orig_name, kor_name in translations.items():
        if orig_name == kor_name:
            continue

        escaped = orig_name.replace('%', '\\%').replace('_', '\\_')

        cur.execute(
            "SELECT id, cast_ko FROM movies WHERE cast_ko LIKE %s ESCAPE '\\'",
            (f'%{escaped}%',)
        )

        for movie_id, cast_ko in cur.fetchall():
            names = [n.strip() for n in cast_ko.split(',')]
            updated_names = []
            changed = False

            for name in names:
                if name == orig_name:
                    updated_names.append(kor_name)
                    changed = True
                else:
                    updated_names.append(name)

            if changed:
                new_cast_ko = ', '.join(updated_names)
                cur.execute(
                    "UPDATE movies SET cast_ko = %s WHERE id = %s",
                    (new_cast_ko, movie_id)
                )
                total_updated += 1

    conn.commit()
    return total_updated


# ===== 5. 메인 =====

def main():
    parser = argparse.ArgumentParser(description='cast_ko 외국어 이름 → 한글 음역 변환')
    parser.add_argument('--dry-run', action='store_true',
                        help='영향 범위만 확인 (API 호출/DB 변경 없음)')
    parser.add_argument('--resume', action='store_true', default=True,
                        help='이전 진행 상태에서 재개 (기본값: True)')
    parser.add_argument('--no-resume', dest='resume', action='store_false',
                        help='처음부터 다시 시작')
    args = parser.parse_args()

    print("=" * 70)
    print("cast_ko 외국어 이름 → 한글 음역 변환 (중국어/일본어/그리스어/라틴 등)")
    print(f"  모드: {'DRY RUN (확인만)' if args.dry_run else '실행'}")
    print(f"  재개: {'ON' if args.resume else 'OFF'}")
    print(f"  배치 크기: {BATCH_SIZE}")
    print("=" * 70)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print("\nDB 연결 완료")

    # ── Step 1: 외국어 이름 추출 ──
    print("\n[1/4] 외국어 이름 추출 중...")
    name_freq, name_type = extract_foreign_names(conn)
    print(f"  비한글 이름 총: {len(name_freq):,}개")

    # 스크립트별 통계
    type_counts = {}
    for name, ntype in name_type.items():
        label = ntype or 'unknown'
        type_counts[label] = type_counts.get(label, 0) + 1
    print(f"\n  스크립트별 분포:")
    for label in sorted(type_counts.keys()):
        print(f"    {label:20s}: {type_counts[label]:,}개")

    # ── Step 2: 진행 상태 로드 ──
    print("\n[2/4] 진행 상태 확인...")
    progress = load_progress() if args.resume else {
        "translated": {}, "failed_batches": [],
        "total_input_tokens": 0, "total_output_tokens": 0,
    }

    already_done = set(progress["translated"].keys())
    actual_translations = {k: v for k, v in progress["translated"].items() if k != v}
    print(f"  이미 번역된 이름: {len(already_done):,}개 (실제 변환: {len(actual_translations):,}개)")

    # 미번역 이름 (빈도 높은 순)
    remaining = [(name, name_freq[name]) for name in name_freq if name not in already_done]
    remaining.sort(key=lambda x: -x[1])
    remaining_names = [name for name, _ in remaining]
    print(f"  남은 이름: {len(remaining_names):,}개")

    if not remaining_names:
        print("\n  모든 이름이 번역 완료되었습니다!")
        conn.close()
        return

    # ── Step 3: 처리 예상 ──
    total_batches = (len(remaining_names) + BATCH_SIZE - 1) // BATCH_SIZE
    est_input_tokens = total_batches * 2000
    est_output_tokens = total_batches * 1500
    est_cost = (est_input_tokens * 3 + est_output_tokens * 15) / 1_000_000

    print(f"\n  처리 계획:")
    print(f"    배치 수: {total_batches}회")
    print(f"    예상 비용: ~${est_cost:.2f}")

    if args.dry_run:
        print("\n[DRY RUN] 여기서 종료합니다.")
        print(f"\n  변환 대상 샘플 (Top 30 - 빈도 높은 순):")
        for name, count in remaining[:30]:
            ntype = name_type.get(name, '?')
            print(f"    [{ntype:15s}] {name} ({count}편)")
        conn.close()
        return

    # ── Step 4: Claude API 배치 처리 ──
    print(f"\n[3/4] Claude API 배치 처리 시작...")
    total_movies_updated = 0
    batch_success = 0
    batch_fail = 0
    start_time = time.time()

    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(remaining_names))
        batch_names = remaining_names[start:end]

        elapsed = time.time() - start_time
        if batch_idx > 0:
            avg_per_batch = elapsed / batch_idx
            eta_sec = avg_per_batch * (total_batches - batch_idx)
            eta_min = int(eta_sec // 60)
            eta_s = int(eta_sec % 60)
            eta_str = f"ETA {eta_min}m{eta_s}s"
        else:
            eta_str = "calculating..."

        if batch_idx < 5 or batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            done_count = len(progress["translated"])
            print(f"\n  배치 {batch_idx+1:3d}/{total_batches} "
                  f"(완료 {done_count:,}/{len(name_freq):,}) [{eta_str}]")

        translations, inp_tok, out_tok = transliterate_batch(batch_names)

        if not translations:
            batch_fail += 1
            progress["failed_batches"].append({
                "batch_idx": batch_idx,
                "names": batch_names,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_progress(progress)
            continue

        batch_success += 1

        actual = {k: v for k, v in translations.items() if k != v}
        samples = list(actual.items())[:3]
        for orig, kor in samples:
            print(f"    {orig} → {kor}")
        if len(actual) > 3:
            print(f"    ... 외 {len(actual)-3}개")

        updated = update_db_with_translations(conn, translations)
        total_movies_updated += updated

        if batch_idx < 5 or batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            print(f"    → DB 업데이트: {updated}편 영화")

        progress["translated"].update(translations)
        progress["total_input_tokens"] += inp_tok
        progress["total_output_tokens"] += out_tok
        save_progress(progress)

        if batch_idx < total_batches - 1:
            time.sleep(1)

    # ── Step 5: 최종 통계 ──
    elapsed_total = time.time() - start_time
    total_translated = len(progress["translated"])
    actual_converted = sum(1 for k, v in progress["translated"].items() if k != v)

    print(f"\n{'=' * 70}")
    print(f"[4/4] 완료!")
    print(f"{'=' * 70}")
    print(f"  소요 시간: {int(elapsed_total//60)}m {int(elapsed_total%60)}s")
    print(f"  성공 배치: {batch_success}/{total_batches}")
    print(f"  실패 배치: {batch_fail}")
    print(f"\n  이름 통계:")
    print(f"    처리 대상: {len(name_freq):,}개")
    print(f"    번역 완료: {total_translated:,}개")
    print(f"    실제 변환: {actual_converted:,}개 (한글화)")
    print(f"    원래 유지: {total_translated - actual_converted:,}개")
    print(f"\n  DB 업데이트:")
    print(f"    영화 수: {total_movies_updated:,}편")

    inp_tokens = progress["total_input_tokens"]
    out_tokens = progress["total_output_tokens"]
    input_cost = inp_tokens * 3.0 / 1_000_000
    output_cost = out_tokens * 15.0 / 1_000_000
    total_cost = input_cost + output_cost

    print(f"\n  API 비용:")
    print(f"    Input tokens:  {inp_tokens:>10,} (${input_cost:.3f})")
    print(f"    Output tokens: {out_tokens:>10,} (${output_cost:.3f})")
    print(f"    Total cost:    ${total_cost:.3f}")

    # DB 최종 확인
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM movies WHERE cast_ko IS NOT NULL AND cast_ko != ''")
    total_with_cast = cur.fetchone()[0]

    # 비한글 이름 남은 영화 재확인
    cur.execute("SELECT id, cast_ko FROM movies WHERE cast_ko IS NOT NULL AND cast_ko != ''")
    still_foreign = 0
    for _, cast_ko in cur.fetchall():
        for name in cast_ko.split(','):
            name = name.strip()
            if name and not is_fully_korean(name):
                still_foreign += 1
                break

    print(f"\n  DB 현황:")
    print(f"    cast_ko 있는 영화: {total_with_cast:,}편")
    print(f"    외국어 이름 남은 영화: {still_foreign:,}편")
    print(f"    완전 한글화 영화: {total_with_cast - still_foreign:,}편 ({(total_with_cast - still_foreign)/total_with_cast*100:.1f}%)")

    if progress["failed_batches"]:
        print(f"\n  실패한 배치: {len(progress['failed_batches'])}개")
        print(f"  재실행하면 실패한 이름도 재시도됩니다.")

    conn.close()
    print(f"\n진행 파일: {PROGRESS_FILE}")
    print("Done!")


if __name__ == "__main__":
    main()
