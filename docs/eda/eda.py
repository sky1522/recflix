import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. 데이터 로드
file_path = 'MOVIE_FINAL_FIXED_TITLES.csv'
df = pd.read_csv(file_path)

# 한글 폰트 설정 (Windows 기준: 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 기본 정보 확인
print(f"--- 데이터셋 크기: {df.shape} ---")
print("\n--- 누락된 데이터(결측치) 확인 ---")
print(df.isnull().sum()[df.isnull().sum() > 0])

# 3. 주요 수치 데이터 분석 (평점, 투표수, 인기도, 상영시간)
critical_cols = ['vote_average', 'vote_count', 'popularity', 'runtime']
print("\n--- 주요 수치 통계 ---")
print(df[critical_cols].describe())

# 4. 시각화: 수치형 데이터 분포
plt.figure(figsize=(15, 10))

plt.subplot(2, 2, 1)
sns.histplot(df['vote_average'], bins=20, kde=True, color='skyblue')
plt.title('평점(Vote Average) 분포')

plt.subplot(2, 2, 2)
sns.histplot(df['vote_count'], bins=50, kde=True, color='salmon')
plt.yscale('log') # 투표수는 편차가 커서 로그 스케일 적용
plt.title('투표수(Vote Count) 분포 (Log Scale)')

plt.subplot(2, 2, 3)
sns.histplot(df['popularity'], bins=50, kde=True, color='green')
plt.yscale('log')
plt.title('인기도(Popularity) 분포 (Log Scale)')

plt.subplot(2, 2, 4)
sns.histplot(df['runtime'], bins=30, kde=True, color='purple')
plt.title('상영시간(Runtime) 분포')

plt.tight_layout()
plt.savefig('numerical_distributions.png')

# 5. 장르 분포 분석 (One-hot encoded 컬럼 활용)
genre_columns = [
    'SF', 'TV 영화', '가족', '공포', '다큐멘터리', '드라마', '로맨스', '모험', '미스터리',
    '범죄', '서부', '스릴러', '애니메이션', '액션', '역사', '음악', '전쟁', '코미디', '판타지'
]
genre_counts = df[genre_columns].sum().sort_values(ascending=False)

plt.figure(figsize=(12, 6))
sns.barplot(x=genre_counts.values, y=genre_counts.index, palette='viridis')
plt.title('장르별 영화 편수')
plt.xlabel('영화 수')
plt.tight_layout()
plt.savefig('genre_distribution.png')

# 6. 상관관계 분석
plt.figure(figsize=(10, 8))
corr = df[critical_cols + ['is_adult']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('변수 간 상관관계 히트맵')
plt.tight_layout()
plt.savefig('correlation_heatmap.png')

print("\nEDA 완료: 'numerical_distributions.png', 'genre_distribution.png', 'correlation_heatmap.png' 파일이 생성되었습니다.")