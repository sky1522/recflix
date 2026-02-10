import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. 데이터 로드
file_path = 'MOVIE_total_FINAL_FINAL_2010.csv'
df = pd.read_csv(file_path)

# 한글 폰트 설정 (Windows 기준: 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 기본 정보 확인
print(f"--- 데이터셋 크기: {df.shape} ---")
print(f"\n--- 컬럼 목록 ({len(df.columns)}개) ---")
print(df.columns.tolist())
print("\n--- 누락된 데이터(결측치) 확인 ---")
missing = df.isnull().sum()[df.isnull().sum() > 0]
print(missing if len(missing) > 0 else "결측치 없음")

# 3. 주요 수치 데이터 분석 (평점, 투표수, 인기도, 상영시간, 가중평점)
critical_cols = ['vote_average', 'vote_count', 'popularity', 'runtime', 'weighted_score']
print("\n--- 주요 수치 통계 ---")
print(df[critical_cols].describe())

# 4. 시각화: 수치형 데이터 분포
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

sns.histplot(df['vote_average'], bins=20, kde=True, color='skyblue', ax=axes[0, 0])
axes[0, 0].set_title('평점(Vote Average) 분포')

sns.histplot(df['vote_count'], bins=50, kde=True, color='salmon', ax=axes[0, 1])
axes[0, 1].set_yscale('log')
axes[0, 1].set_title('투표수(Vote Count) 분포 (Log Scale)')

sns.histplot(df['popularity'], bins=50, kde=True, color='green', ax=axes[0, 2])
axes[0, 2].set_yscale('log')
axes[0, 2].set_title('인기도(Popularity) 분포 (Log Scale)')

sns.histplot(df['runtime'], bins=30, kde=True, color='purple', ax=axes[1, 0])
axes[1, 0].set_title('상영시간(Runtime) 분포')

sns.histplot(df['weighted_score'], bins=20, kde=True, color='orange', ax=axes[1, 1])
axes[1, 1].set_title('가중평점(Weighted Score) 분포')

# 개봉 계절 분포
season_order = ['봄', '여름', '가을', '겨울']
season_counts = df['release_season'].value_counts().reindex(season_order)
sns.barplot(x=season_counts.index, y=season_counts.values, palette='coolwarm', ax=axes[1, 2])
axes[1, 2].set_title('개봉 계절 분포')
axes[1, 2].set_xlabel('계절')
axes[1, 2].set_ylabel('영화 수')

plt.tight_layout()
plt.savefig('numerical_distributions.png', dpi=150)
print("\n[저장] numerical_distributions.png")

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
plt.savefig('genre_distribution.png', dpi=150)
print("[저장] genre_distribution.png")

# 6. 연령 등급(Certification) 분포
plt.figure(figsize=(10, 5))
cert_counts = df['certification'].value_counts().head(10)
sns.barplot(x=cert_counts.values, y=cert_counts.index, palette='Set2')
plt.title('연령 등급(Certification) 분포 (상위 10개)')
plt.xlabel('영화 수')
plt.tight_layout()
plt.savefig('certification_distribution.png', dpi=150)
print("[저장] certification_distribution.png")

# 7. 상관관계 분석
plt.figure(figsize=(10, 8))
corr_cols = ['vote_average', 'vote_count', 'popularity', 'runtime', 'weighted_score', 'is_adult']
corr = df[corr_cols].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('변수 간 상관관계 히트맵')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=150)
print("[저장] correlation_heatmap.png")

# 8. 연도별 영화 편수 추이
df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
yearly = df['release_year'].value_counts().sort_index()

plt.figure(figsize=(14, 5))
yearly.plot(kind='bar', color='steelblue', width=0.8)
plt.title('연도별 영화 편수')
plt.xlabel('연도')
plt.ylabel('영화 수')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('yearly_distribution.png', dpi=150)
print("[저장] yearly_distribution.png")

# 9. 장르별 평균 평점
genre_avg = {}
for g in genre_columns:
    genre_avg[g] = df[df[g] == 1]['vote_average'].mean()
genre_avg_series = pd.Series(genre_avg).sort_values(ascending=False)

plt.figure(figsize=(12, 6))
sns.barplot(x=genre_avg_series.values, y=genre_avg_series.index, palette='magma')
plt.title('장르별 평균 평점')
plt.xlabel('평균 평점')
plt.tight_layout()
plt.savefig('genre_avg_rating.png', dpi=150)
print("[저장] genre_avg_rating.png")

print("\n✅ EDA 완료! 생성된 파일:")
print("  - numerical_distributions.png")
print("  - genre_distribution.png")
print("  - certification_distribution.png")
print("  - correlation_heatmap.png")
print("  - yearly_distribution.png")
print("  - genre_avg_rating.png")