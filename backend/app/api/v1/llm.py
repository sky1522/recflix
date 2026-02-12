"""
LLM API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import Movie
from app.schemas.llm import CatchphraseResponse
from app.services.llm import generate_catchphrase

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/catchphrase/{movie_id}", response_model=CatchphraseResponse)
async def get_catchphrase(movie_id: int, db: Session = Depends(get_db)):
    """
    영화에 대한 LLM 생성 캐치프레이즈 조회

    - Redis 캐시 확인 (24시간 TTL)
    - 캐시 미스 시 OpenAI GPT-4o-mini로 생성
    - 에러 시 기존 tagline 반환
    """
    # 영화 정보 조회
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")

    # 장르명 추출
    genre_names = [g.name_ko or g.name for g in movie.genres] if movie.genres else []

    # 캐치프레이즈 생성
    catchphrase, cached = await generate_catchphrase(
        movie_id=movie.id,
        title=movie.title_ko or movie.title,
        overview=movie.overview or "",
        genres=genre_names,
        fallback_tagline=movie.tagline,
    )

    return CatchphraseResponse(
        movie_id=movie_id,
        catchphrase=catchphrase,
        cached=cached,
    )
