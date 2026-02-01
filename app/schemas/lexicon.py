from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class LexiconSentimentLabel(str, Enum):
    POSITIF = "Positif"
    NEGATIF = "Negatif"
    NETRAL = "Netral"


# ============================================================
# Request Schemas
# ============================================================

class LexiconPredictRequest(BaseModel):
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


class LexiconSinglePredictRequest(BaseModel):
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

class LexiconPrediction(BaseModel):
    """Single prediction result."""
    label: LexiconSentimentLabel = Field(..., description="Predicted sentiment label")
    score: float = Field(..., description="Sentiment score (positive = positif, negative = negatif)")
    tokens: List[str] = Field(..., description="Preprocessed tokens")
    matched_words: Dict[str, float] = Field(default_factory=dict, description="Words found in lexicon with their scores")


class LexiconPredictResponse(BaseModel):
    """Response untuk batch prediction."""
    predictions: List[LexiconPrediction]


class LexiconSinglePredictResponse(BaseModel):
    """Response untuk single prediction."""
    text: str
    label: LexiconSentimentLabel
    score: float
    tokens: List[str]
    matched_words: Dict[str, float]


# ============================================================
# Analyze Post Comments Schemas
# ============================================================

class LexiconCommentResult(BaseModel):
    """Result untuk satu komentar yang sudah dianalisis."""
    comment_id: str
    text: str
    label: LexiconSentimentLabel
    score: float
    tokens: List[str]


class LexiconAnalyzePostResponse(BaseModel):
    """Response untuk analyze post comments endpoint."""
    success: bool
    post_id: str
    total_comments: int
    analyzed_count: int
    results: List[LexiconCommentResult]
    summary: Dict[str, int] = Field(..., description="Count per sentiment label")
    message: str
