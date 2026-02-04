"""
LLM Schemas
"""
from pydantic import BaseModel


class CatchphraseResponse(BaseModel):
    """캐치프레이즈 응답"""
    movie_id: int
    catchphrase: str
    cached: bool = False
