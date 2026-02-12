"""
persons 테이블 영어 배우 이름 → 한글 음역 변환 스크립트

대상: persons 테이블의 영어 이름 (cast_ko 변환 매핑에 없는 이름)
방식: Claude API 배치 처리 (50개/배치)
저장: 배치별 즉시 DB 저장 + JSON 진행 파일로 중단/재개 지원

사용법:
  cd backend
  ./venv/Scripts/python.exe scripts/transliterate_persons.py           # 실행
  ./venv/Scripts/python.exe scripts/transliterate_persons.py --dry-run # 확인만
  ./venv/Scripts/python.exe scripts/transliterate_persons.py --resume  # 재개
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
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persons_transliteration_progress.json")


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data.setdefault("translated", {})
            data.setdefault("failed_batches", [])
            data.setdefault("total_input_tokens", 0)
            data.setdefault("total_output_tokens", 0)
            return data
    return {"translated": {}, "failed_batches": [],
            "total_input_tokens": 0, "total_output_tokens": 0}


def save_progress(progress):
    tmp_file = PROGRESS_FILE + ".tmp"
    try:
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        os.rename(tmp_file, PROGRESS_FILE)
    except OSError as e:
        print(f"    [WARN] 진행 파일 저장 실패: {e}")
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass


def transliterate_batch(names, retry=0):
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

2. Indian/Hindi names → Korean based on original pronunciation
   "Prakash Raj" → "프라카시 라지"
   "Amitabh Bachchan" → "아미타브 바찬"

3. Chinese names → Korean based on Chinese pronunciation
   "Zhang Ziyi" → "장쯔이"
   "Jackie Chan" → "재키 찬"

4. Japanese names → Korean based on Japanese pronunciation
   "Takeshi Kitano" → "기타노 다케시"

5. Spanish/French/German accented names → reflect original pronunciation
   "Javier Bardem" → "하비에르 바르뎀"
   "Gérard Depardieu" → "제라르 드파르디외"

6. Initials → keep as-is + transliterate the rest
   "A.J. Cook" → "A.J. 쿡"
   "J.K. Simmons" → "J.K. 시몬스"

7. Stage names with numbers/symbols → transliterate the word part
   "50 Cent" → "50 센트"

8. Single-word names → transliterate as-is
   "Mammootty" → "맘무티"

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

        return translations, response.usage.input_tokens, response.usage.output_tokens

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


def main():
    parser = argparse.ArgumentParser(description='persons 테이블 영어 이름 → 한글 음역 변환')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--resume', action='store_true', default=True)
    parser.add_argument('--no-resume', dest='resume', action='store_false')
    args = parser.parse_args()

    print("=" * 70)
    print("persons 테이블 영어 배우 이름 → 한글 음역 변환")
    print(f"  모드: {'DRY RUN' if args.dry_run else '실행'}")
    print(f"  재개: {'ON' if args.resume else 'OFF'}")
    print("=" * 70)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    print("\nDB 연결 완료")

    # 영어 이름 persons 추출
    print("\n[1/3] 영어 이름 추출 중...")
    cur.execute("""
        SELECT id, name FROM persons
        WHERE name ~ '[A-Za-z]' AND name !~ '^[가-힣 ]+$'
    """)
    english_persons = {row[0]: row[1] for row in cur.fetchall()}
    print(f"  영어 이름 persons: {len(english_persons):,}명")

    # 진행 상태 로드
    print("\n[2/3] 진행 상태 확인...")
    progress = load_progress() if args.resume else {
        "translated": {}, "failed_batches": [],
        "total_input_tokens": 0, "total_output_tokens": 0,
    }

    already_done = set(progress["translated"].keys())
    print(f"  이미 번역됨: {len(already_done):,}개")

    # 미처리 persons (이름 기준 중복 제거)
    remaining_names = {}
    for pid, name in english_persons.items():
        if name not in already_done and name not in remaining_names:
            remaining_names[name] = pid

    remaining_list = sorted(remaining_names.keys())
    print(f"  남은 고유 이름: {len(remaining_list):,}개")

    if not remaining_list:
        print("\n  모든 이름이 번역 완료!")
        conn.close()
        return

    total_batches = (len(remaining_list) + BATCH_SIZE - 1) // BATCH_SIZE
    est_cost = total_batches * (2000 * 3 + 1500 * 15) / 1_000_000
    print(f"\n  배치 수: {total_batches}회")
    print(f"  예상 비용: ~${est_cost:.2f}")

    if args.dry_run:
        print("\n[DRY RUN] 종료.")
        print(f"\n  샘플 (20개):")
        for name in remaining_list[:20]:
            print(f"    {name}")
        conn.close()
        return

    # 배치 처리
    print(f"\n[3/3] Claude API 배치 처리 시작...")
    total_updated = 0
    start_time = time.time()

    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(remaining_list))
        batch_names = remaining_list[start:end]

        elapsed = time.time() - start_time
        if batch_idx > 0:
            eta_sec = (elapsed / batch_idx) * (total_batches - batch_idx)
            eta_str = f"ETA {int(eta_sec//60)}m{int(eta_sec%60)}s"
        else:
            eta_str = "calculating..."

        done_total = len(progress["translated"])
        if batch_idx < 5 or batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            print(f"\n  배치 {batch_idx+1:3d}/{total_batches} "
                  f"(완료 {done_total:,}) [{eta_str}]")

        translations, inp_tok, out_tok = transliterate_batch(batch_names)

        if not translations:
            progress["failed_batches"].append({
                "batch_idx": batch_idx, "names": batch_names,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_progress(progress)
            continue

        # DB 업데이트: persons 테이블
        batch_updated = 0
        for eng_name, kor_name in translations.items():
            if eng_name == kor_name:
                continue
            # 같은 이름의 모든 persons 업데이트
            cur.execute("UPDATE persons SET name = %s WHERE name = %s", (kor_name, eng_name))
            batch_updated += cur.rowcount

        conn.commit()
        total_updated += batch_updated

        # 샘플 출력
        actual = {k: v for k, v in translations.items() if k != v}
        samples = list(actual.items())[:3]
        for eng, kor in samples:
            print(f"    {eng} → {kor}")
        if len(actual) > 3:
            print(f"    ... 외 {len(actual)-3}개")

        if batch_idx < 5 or batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            print(f"    → persons 업데이트: {batch_updated}명")

        # 진행 저장
        progress["translated"].update(translations)
        progress["total_input_tokens"] += inp_tok
        progress["total_output_tokens"] += out_tok
        save_progress(progress)

        if batch_idx < total_batches - 1:
            time.sleep(1)

    # 최종 통계
    elapsed_total = time.time() - start_time
    inp = progress["total_input_tokens"]
    out = progress["total_output_tokens"]
    cost = (inp * 3 + out * 15) / 1_000_000

    print(f"\n{'=' * 70}")
    print(f"완료!")
    print(f"{'=' * 70}")
    print(f"  소요 시간: {int(elapsed_total//60)}m {int(elapsed_total%60)}s")
    print(f"  persons 업데이트: {total_updated:,}명")
    print(f"  API 비용: ${cost:.3f}")

    cur.execute("SELECT COUNT(*) FROM persons WHERE name ~ '[A-Za-z]'")
    remaining_eng = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM persons")
    total_persons = cur.fetchone()[0]
    print(f"\n  persons 현황:")
    print(f"    전체: {total_persons:,}명")
    print(f"    한글화: {total_persons - remaining_eng:,}명 ({(total_persons-remaining_eng)/total_persons*100:.1f}%)")
    print(f"    영어 남은: {remaining_eng:,}명")

    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
