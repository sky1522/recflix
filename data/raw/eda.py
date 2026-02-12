import pandas as pd

# 1. 파일 불러오기
df = pd.read_csv('MOVIE_total_FINAL_FINAL_2010.csv')

# 2. popularity 컬럼의 기초 통계량 확인
# 결과는 데이터 개수, 평균, 표준편차, 최솟값, 4분위수, 최댓값 순으로 출력됩니다.
print(df['popularity'].describe())