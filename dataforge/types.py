from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[str] = None
    source_score: Optional[float] = None


class TavilySearchResult(BaseModel):
    query: str
    documents: List[SourceDocument] = Field(default_factory=list)
    total_results: int = 0


class GPTQualityScores(BaseModel):
    factual_accuracy: Optional[float] = None
    coherence: Optional[float] = None
    educational_value: Optional[float] = None
    writing_quality: Optional[float] = None
    originality: Optional[float] = None


class GPTAnalysisResult(BaseModel):
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    scores: Optional[GPTQualityScores] = None
    raw: Optional[Dict] = None
