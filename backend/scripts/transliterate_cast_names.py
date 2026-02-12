"""
cast_ko 영어 배우 이름 → 한글 음역 변환 스크립트

대상: 모든 순수 영어 배우 이름 (1편 포함, 총 ~33,529개)
방식: Claude API 배치 처리 (50개/배치)
저장: 배치별 즉시 DB 저장 + JSON 진행 파일로 중단/재개 지원

사용법:
  cd backend
  ./venv/Scripts/python.exe scripts/transliterate_cast_names.py           # 실행
  ./venv/Scripts/python.exe scripts/transliterate_cast_names.py --dry-run # 영향 범위만 확인
  ./venv/Scripts/python.exe scripts/transliterate_cast_names.py --resume  # 중단 후 재개

진행 파일: backend/scripts/cast_transliteration_progress.json
"""
import os, sys, json, time, io, re, argparse
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
MIN_MOVIE_COUNT = 1
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cast_transliteration_progress.json")


# ===== 1. 영어 이름 추출 =====

def extract_english_names(conn):
    """DB에서 cast_ko의 순수 영어 배우 이름과 등장 빈도 추출"""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, cast_ko FROM movies
        WHERE cast_ko IS NOT NULL AND cast_ko != '' AND cast_ko ~ '[A-Za-z]'
    """)

    name_freq = {}
    for movie_id, cast_ko in cur.fetchall():
        names = [n.strip() for n in cast_ko.split(',')]
        for name in names:
            if not name:
                continue
            has_eng = bool(re.search(r'[A-Za-z]', name))
            has_kor = bool(re.search(r'[가-힣]', name))
            if has_eng and not has_kor:
                name_freq[name] = name_freq.get(name, 0) + 1

    # MIN_MOVIE_COUNT 이상 등장하는 이름만 반환
    return {name: count for name, count in name_freq.items() if count >= MIN_MOVIE_COUNT}


# ===== 2. 진행 상태 관리 =====

def load_progress():
    """이전 진행 상태 로드"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 기본 키 보장
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
    """진행 상태 저장 (임시 파일 → rename으로 안전 쓰기)"""
    tmp_file = PROGRESS_FILE + ".tmp"
    try:
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        # Windows: 기존 파일 삭제 후 rename
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        os.rename(tmp_file, PROGRESS_FILE)
    except OSError as e:
        print(f"    [WARN] 진행 파일 저장 실패: {e} (DB는 정상 반영됨)")
        # tmp 파일 정리
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass


# ===== 3. Claude API 음역 변환 =====

def transliterate_batch(names, retry=0):
    """Claude API로 영어 이름 배치를 한글 음역 변환

    Args:
        names: 변환할 영어 이름 리스트 (최대 50개)
        retry: 재시도 횟수

    Returns:
        (translations_dict, input_tokens, output_tokens)
    """
    names_text = "\n".join(f"{i+1}. {name}" for i, name in enumerate(names))

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system="""You are an expert transliterator. Convert foreign names to Korean (한글) phonetic transliteration.

RULES:
1. English names → Korean based on English pronunciation
   "Bruce Davison" → "브루스 데이비슨"
   "Robert De Niro" → "로버트 드 니로"
   "Scarlett Johansson" → "스칼렛 요한슨"

2. Indian/Hindi names → Korean based on original pronunciation
   "Prakash Raj" → "프라카시 라지"
   "Amitabh Bachchan" → "아미타브 바찬"
   "Rajinikanth" → "라지니칸트"

3. Chinese names → Korean based on Chinese pronunciation
   "Zhang Ziyi" → "장쯔이"
   "Jackie Chan" → "재키 찬"
   "Jet Li" → "제트 리"

4. Japanese names → Korean based on Japanese pronunciation
   "Takeshi Kitano" → "기타노 다케시"

5. Spanish/French/German accented names → reflect original pronunciation
   "Javier Bardem" → "하비에르 바르뎀"
   "Gérard Depardieu" → "제라르 드파르디외"
   "Martínez" → "마르티네스"

6. Initials → keep as-is + transliterate the rest
   "A.J. Cook" → "A.J. 쿡"
   "J.K. Simmons" → "J.K. 시몬스"

7. Stage names with numbers/symbols → transliterate the word part
   "50 Cent" → "50 센트"
   "Ice-T" → "아이스-T"

8. Single-word names → transliterate as-is
   "Mammootty" → "맘무티"
   "Brahmanandam" → "브라흐마난담"

Return ONLY valid JSON: {"original_name": "한글음역", ...}
No explanation, no markdown, just pure JSON.""",
            messages=[{
                "role": "user",
                "content": f"Convert these {len(names)} names to Korean transliteration:\n\n{names_text}"
            }]
        )

        content = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)

        # 검증: 입력 이름과 매칭 확인
        translations = {}
        for name in names:
            if name in result:
                kor = result[name].strip()
                # 변환 결과에 한글이 포함되어 있는지 확인
                if re.search(r'[가-힣]', kor):
                    translations[name] = kor
                else:
                    # 한글 변환 실패 → 원래 이름 유지
                    translations[name] = name
            else:
                # API 응답에 누락된 이름 → 원래 이름 유지
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
    """번역 결과를 DB의 cast_ko에 반영

    각 영어 이름에 대해:
    1) LIKE로 해당 이름을 포함하는 영화 검색
    2) cast_ko를 쉼표로 분리 → 정확 매칭으로 교체 → 재결합
    3) 변경된 영화만 UPDATE

    Returns: 업데이트된 영화 수
    """
    cur = conn.cursor()
    total_updated = 0

    for eng_name, kor_name in translations.items():
        # 변환되지 않은 이름 (원래 이름 그대로) 건너뛰기
        if eng_name == kor_name:
            continue

        # LIKE 특수문자 이스케이프
        escaped = eng_name.replace('%', '\\%').replace('_', '\\_')

        cur.execute(
            "SELECT id, cast_ko FROM movies WHERE cast_ko LIKE %s ESCAPE '\\'",
            (f'%{escaped}%',)
        )

        for movie_id, cast_ko in cur.fetchall():
            names = [n.strip() for n in cast_ko.split(',')]
            updated_names = []
            changed = False

            for name in names:
                if name == eng_name:
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
    parser = argparse.ArgumentParser(description='cast_ko 영어 배우 이름 → 한글 음역 변환')
    parser.add_argument('--dry-run', action='store_true',
                        help='영향 범위만 확인 (API 호출/DB 변경 없음)')
    parser.add_argument('--resume', action='store_true', default=True,
                        help='이전 진행 상태에서 재개 (기본값: True)')
    parser.add_argument('--no-resume', dest='resume', action='store_false',
                        help='처음부터 다시 시작')
    args = parser.parse_args()

    print("=" * 70)
    print("cast_ko 영어 배우 이름 → 한글 음역 변환")
    print(f"  모드: {'DRY RUN (확인만)' if args.dry_run else '실행'}")
    print(f"  재개: {'ON' if args.resume else 'OFF'}")
    print(f"  배치 크기: {BATCH_SIZE}")
    print(f"  최소 등장 횟수: {MIN_MOVIE_COUNT}편")
    print("=" * 70)

    # DB 연결
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print("\nDB 연결 완료")

    # ── Step 1: 영어 이름 추출 ──
    print("\n[1/4] 영어 배우 이름 추출 중...")
    name_freq = extract_english_names(conn)
    print(f"  {MIN_MOVIE_COUNT}편 이상 등장하는 영어 이름: {len(name_freq):,}개")

    # 빈도 분포 통계
    freq_dist = {}
    for count in name_freq.values():
        bucket = f"{count}편" if count <= 10 else "11편+"
        freq_dist[bucket] = freq_dist.get(bucket, 0) + 1
    print(f"\n  등장 빈도 분포:")
    for bucket in sorted(freq_dist.keys()):
        print(f"    {bucket}: {freq_dist[bucket]:,}개")

    # ── Step 2: 진행 상태 로드 ──
    print("\n[2/4] 진행 상태 확인...")
    progress = load_progress() if args.resume else {
        "translated": {}, "failed_batches": [],
        "total_input_tokens": 0, "total_output_tokens": 0,
    }

    already_done = set(progress["translated"].keys())
    # 이미 번역된 이름 중 실제 변환된 것만 카운트
    actual_translations = {k: v for k, v in progress["translated"].items() if k != v}
    print(f"  이미 번역된 이름: {len(already_done):,}개 (실제 변환: {len(actual_translations):,}개)")

    # 미번역 이름 (빈도 높은 순으로 정렬)
    remaining = [(name, name_freq[name]) for name in name_freq if name not in already_done]
    remaining.sort(key=lambda x: -x[1])  # 빈도 높은 순
    remaining_names = [name for name, _ in remaining]
    print(f"  남은 이름: {len(remaining_names):,}개")

    if not remaining_names:
        print("\n  모든 이름이 번역 완료되었습니다!")
        conn.close()
        return

    # ── Step 3: 처리 예상 ──
    total_batches = (len(remaining_names) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n  처리 계획:")
    print(f"    배치 수: {total_batches}회")
    print(f"    예상 API 호출: {total_batches}회")

    # Sonnet pricing: $3/M input, $15/M output
    est_input_tokens = total_batches * 2000   # ~2K input per batch
    est_output_tokens = total_batches * 1500  # ~1.5K output per batch
    est_cost = (est_input_tokens * 3 + est_output_tokens * 15) / 1_000_000
    print(f"    예상 비용: ~${est_cost:.2f}")

    if args.dry_run:
        print("\n[DRY RUN] 여기서 종료합니다. --dry-run 없이 실행하면 변환이 시작됩니다.")

        # 샘플 출력
        print(f"\n  변환 대상 샘플 (Top 20 - 빈도 높은 순):")
        for name, count in remaining[:20]:
            print(f"    {name} ({count}편)")

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

        # ETA 계산
        elapsed = time.time() - start_time
        if batch_idx > 0:
            avg_per_batch = elapsed / batch_idx
            eta_sec = avg_per_batch * (total_batches - batch_idx)
            eta_min = int(eta_sec // 60)
            eta_s = int(eta_sec % 60)
            eta_str = f"ETA {eta_min}m{eta_s}s"
        else:
            eta_str = "calculating..."

        # 진행 상태 출력 (처음 5개, 10개마다, 마지막)
        if batch_idx < 5 or batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            done_count = len(progress["translated"])
            print(f"\n  배치 {batch_idx+1:3d}/{total_batches} "
                  f"(완료 {done_count:,}/{len(name_freq):,}) [{eta_str}]")

        # API 호출
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

        # 변환 결과 샘플 출력
        actual = {k: v for k, v in translations.items() if k != v}
        samples = list(actual.items())[:3]
        for eng, kor in samples:
            print(f"    {eng} → {kor}")
        if len(actual) > 3:
            print(f"    ... 외 {len(actual)-3}개")

        # DB 업데이트
        updated = update_db_with_translations(conn, translations)
        total_movies_updated += updated

        if batch_idx < 5 or batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            print(f"    → DB 업데이트: {updated}편 영화")

        # 진행 상태 저장 (DB commit 후)
        progress["translated"].update(translations)
        progress["total_input_tokens"] += inp_tok
        progress["total_output_tokens"] += out_tok
        save_progress(progress)

        # Rate limiting
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

    # API 비용
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
    cur.execute("""
        SELECT COUNT(*) FROM movies
        WHERE cast_ko IS NOT NULL AND cast_ko != '' AND cast_ko ~ '[A-Za-z]'
    """)
    remaining_eng = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM movies WHERE cast_ko IS NOT NULL AND cast_ko != ''")
    total_with_cast = cur.fetchone()[0]

    print(f"\n  DB 현황:")
    print(f"    cast_ko 있는 영화: {total_with_cast:,}편")
    print(f"    영어 이름 남은 영화: {remaining_eng:,}편")
    print(f"    완전 한글화 영화: {total_with_cast - remaining_eng:,}편")

    if progress["failed_batches"]:
        print(f"\n  실패한 배치: {len(progress['failed_batches'])}개")
        print(f"  재실행하면 실패한 이름도 재시도됩니다.")

    conn.close()
    print(f"\n진행 파일: {PROGRESS_FILE}")
    print("Done!")


if __name__ == "__main__":
    main()
