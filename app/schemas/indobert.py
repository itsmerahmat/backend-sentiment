from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class SentimentLabel(str, Enum):
    NEGATIF = "Negatif"
    NETRAL = "Netral"
    POSITIF = "Positif"


# ============================================================
# Request Schemas
# ============================================================

class IndoBertPredictRequest(BaseModel):
    """Request untuk prediksi sentimen batch (multiple texts)."""
    texts: List[str] = Field(..., min_length=1, description="List of texts to analyze")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "texts": ["makanannya enak sekali", "pelayanannya sangat buruk"]
                }
            ]
        }
    }


class IndoBertSinglePredictRequest(BaseModel):
    """Request untuk prediksi sentimen single text."""
    text: str = Field(..., min_length=1, description="Text to analyze")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "makanannya enak sekali"
                }
            ]
        }
    }


# ============================================================
# Response Schemas
# ============================================================

class IndoBertPrediction(BaseModel):
    """Single prediction result."""
    label: SentimentLabel = Field(..., description="Predicted sentiment label")
    score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    scores: Optional[dict] = Field(None, description="All label scores")


class IndoBertPredictResponse(BaseModel):
    """Response untuk batch prediction."""
    predictions: List[IndoBertPrediction]


class IndoBertSinglePredictResponse(BaseModel):
    """Response untuk single prediction."""
    text: str
    label: SentimentLabel
    score: float
    scores: dict = Field(..., description="Scores for all labels")


# ============================================================
# Analyze Post Comments Schemas
# ============================================================

class CommentSentimentResult(BaseModel):
    """Result untuk satu komentar yang sudah dianalisis."""
    comment_id: str
    text: str
    label: SentimentLabel
    score: float
    scores: dict


class AnalyzePostCommentsResponse(BaseModel):
    """Response untuk analyze post comments endpoint."""
    success: bool
    post_id: str
    total_comments: int
    analyzed_count: int
    results: List[CommentSentimentResult]
    summary: dict = Field(..., description="Count per sentiment label: {Positif: n, Negatif: n, Netral: n}")
    message: str
