>>> import pandas as pd
>>> import matplotlib.pyplot as plt
>>> import seaborn as sns
>>> import os
>>> # 1. 데이터 로드
>>> 
>>> file_path = 'MOVIE_FINAL_FIXED_TITLES.csv'
>>> df = pd.read_csv(file_path)
>>> # 한글 폰트 설정 (Windows 기준: 맑은 고딕)   
>>> 
>>> plt.rcParams['font.family'] = 'Malgun Gothic'
>>> plt.rcParams['axes.unicode_minus'] = False   
>>> # 2. 기본 정보 확인
>>>
>>> print(f"--- 데이터셋 크기: {df.shape} ---")
--- 데이터셋 크기: (32625, 41) ---
>>> print("\n--- 누락된 데이터(결측치) 확인 ---")

--- 누락된 데이터(결측치) 확인 ---
>>> print(df.isnull().sum()[df.isnull().sum() > 0])
director         532
overview-ko       83
tagline        26881
poster_path      385
dtype: int64
>>> # 3. 주요 수치 데이터 분석 (평점, 투표수, 인기도, 상영시간)
>>>
>>> critical_cols = ['vote_average', 'vote_count', 'popularity', 'runtime']
>>> print("\n--- 주요 수치 통계 ---")

--- 주요 수치 통계 ---
>>> print(df[critical_cols].describe())
       vote_average    vote_count    popularity       runtime
count  32625.000000  32625.000000  32625.000000  32625.000000
mean       5.915372    516.705011      2.985013     98.922759
std        1.557233   1866.919195      5.513952     33.580467
min        0.000000      0.000000      0.010000      1.000000
25%        5.200000      6.000000      0.640000     86.000000
50%        6.100000     28.000000      2.090000     96.000000
75%        6.900000    186.000000      4.200000    112.000000
max       10.000000  38705.000000    456.000000    999.000000
>>> # 4. 시각화: 수치형 데이터 분포
>>>
>>> plt.figure(figsize=(15, 10))
<Figure size 1500x1000 with 0 Axes>
>>> plt.subplot(2, 2, 1)
<Axes: >
>>> sns.histplot(df['vote_average'], bins=20, kde=True, color='skyblue')
<Axes: xlabel='vote_average', ylabel='Count'>
>>> plt.title('평점(Vote Average) 분포')
Text(0.5, 1.0, '평점(Vote Average) 분포')
>>> plt.subplot(2, 2, 2)
<Axes: >
>>> sns.histplot(df['vote_count'], bins=50, kde=True, color='salmon')
<Axes: xlabel='vote_count', ylabel='Count'>
>>> plt.yscale('log') # 투표수는 편차가 커서 로그 스케일 적용
>>> plt.title('투표수(Vote Count) 분포 (Log Scale)')
Text(0.5, 1.0, '투표수(Vote Count) 분포 (Log Scale)')
>>> plt.subplot(2, 2, 3)
<Axes: >
>>> sns.histplot(df['popularity'], bins=50, kde=True, color='green')
<Axes: xlabel='popularity', ylabel='Count'>
>>> plt.yscale('log')
>>> plt.title('인기도(Popularity) 분포 (Log Scale)')
Text(0.5, 1.0, '인기도(Popularity) 분포 (Log Scale)')
>>> plt.subplot(2, 2, 4)
<Axes: >
>>> sns.histplot(df['runtime'], bins=30, kde=True, color='purple')
<Axes: xlabel='runtime', ylabel='Count'>
>>> plt.title('상영시간(Runtime) 분포')
Text(0.5, 1.0, '상영시간(Runtime) 분포')
>>> plt.tight_layout()
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
Font 'default' does not have a glyph for '\u2212' [U+2212], substituting with a dummy symbol.
>>> plt.savefig('numerical_distributions.png')
>>> # 5. 장르 분포 분석 (One-hot encoded 컬럼 활용)
>>>
>>> genre_columns = [
...     'SF', 'TV 영화', '가족', '공포', '다큐멘터리', '드라마', '로맨스', '모험', '미스터리',
...     '범죄', '서부', '스릴러', '애니메이션', '액션', '역사', '음악', '전쟁', '코미디', '판타지'
... ]
>>>
>>> genre_counts = df[genre_columns].sum().sort_values(ascending=False)
>>> plt.figure(figsize=(12, 6))
<Figure size 1200x600 with 0 Axes>
>>> sns.barplot(x=genre_counts.values, y=genre_counts.index, palette='viridis')
<stdin-47>:1: FutureWarning:

Passing `palette` without assigning `hue` is deprecated and will be removed in v0.14.0. Assign the `y` variable to `hue` and set `legend=False` for the same effect.

<Axes: ylabel='None'>
>>> plt.title('장르별 영화 편수')
Text(0.5, 1.0, '장르별 영화 편수')
>>> plt.xlabel('영화 수')
Text(0.5, 0, '영화 수')
>>> plt.tight_layout()
>>> plt.savefig('genre_distribution.png')
>>> # 6. 상관관계 분석
>>>
>>> plt.figure(figsize=(10, 8))
<Figure size 1000x800 with 0 Axes>
>>> corr = df[critical_cols + ['is_adult']].corr()
>>> sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
<Axes: >
>>> plt.title('변수 간 상관관계 히트맵')
Text(0.5, 1.0, '변수 간 상관관계 히트맵')
>>> plt.tight_layout()
>>> plt.savefig('correlation_heatmap.png')
>>> print("\nEDA 완료: 'numerical_distributions.png', 'genre_distribution.png', 'correlation_heatmap.png' 파일
이 생성되었습니다.")

EDA 완료: 'numerical_distributions.png', 'genre_distribution.png', 'correlation_heatmap.png' 파일이 생성되었습
니다.