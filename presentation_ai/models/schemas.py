from pydantic import BaseModel
from typing import Optional, List

class GenerateRequest(BaseModel):
    topic: str
    slide_count: int = 10
    tone: str = "Professional"      # Professional | Casual | Technical
    sample_titles: Optional[List[str]] = None
    # PDF comes as file upload — handled separately in route

class SlideSchema(BaseModel):
    slide_type: str                 # title | content | comparison | etc.
    title: str
    bullet_points: List[str]
    speaker_notes: Optional[str] = None
    # --- Dynamic Layout Engine Fields ---
    layout_id: Optional[str] = None
    layout_score: Optional[float] = None
    content_type: Optional[str] = None
    zone_content: Optional[dict] = None
    is_continuation: bool = False


class DeckSchema(BaseModel):
    deck_title: str
    slides: List[SlideSchema]
