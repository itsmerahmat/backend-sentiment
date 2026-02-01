"""
Lexicon-based Sentiment Analysis Router

Endpoints untuk analisis sentimen menggunakan metode lexicon/kamus kata.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.dependencies import get_db, get_current_active_user
from app.schemas.lexicon import (
    LexiconPredictRequest,
    LexiconPredictResponse,
    LexiconSinglePredictRequest,
    LexiconSinglePredictResponse,
    LexiconPrediction,
    LexiconSentimentLabel,
    LexiconAnalyzePostResponse,
    LexiconCommentResult,
)
from app.services.lexicon_service import (
    predict_sentiment_lexicon,
    predict_sentiment_lexicon_single,
    get_kamus_positif,
    get_kamus_negatif,
)
from app.services import ig_comment_service, ig_post_service, ig_account_service
from app.models.user import User
from app.models.enums import SentimentLabel as DBSentimentLabel


# Mapping dari Lexicon label ke database enum
LEXICON_TO_DB_LABEL = {
    "Positif": DBSentimentLabel.POSITIVE,
    "Negatif": DBSentimentLabel.NEGATIVE,
    "Netral": DBSentimentLabel.NEUTRAL,
}


router = APIRouter(prefix="/lexicon", tags=["Lexicon Sentiment"])


@router.get("/health")
def health_check():
    """Check if the Lexicon service is ready."""
    kamus_positif = get_kamus_positif()
    kamus_negatif = get_kamus_negatif()
    return {
        "status": "healthy",
        "method": "lexicon-based",
        "positive_words_count": len(kamus_positif),
        "negative_words_count": len(kamus_negatif),
        "total_words": len(kamus_positif) + len(kamus_negatif)
    }


@router.post("/predict", response_model=LexiconPredictResponse)
def predict_batch(payload: LexiconPredictRequest):
    """
    Prediksi sentimen untuk multiple texts (batch) menggunakan metode lexicon.
    
    - **texts**: List of texts untuk dianalisis
    
    Returns predictions dengan label (Negatif/Netral/Positif), score, dan matched words.
    """
    try:
        outputs = predict_sentiment_lexicon(payload.texts)
        predictions = [
            LexiconPrediction(
                label=LexiconSentimentLabel(o["label"]),
                score=o["score"],
                tokens=o["tokens"],
                matched_words=o["matched_words"]
            )
            for o in outputs
        ]
        return LexiconPredictResponse(predictions=predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/single", response_model=LexiconSinglePredictResponse)
def predict_single(payload: LexiconSinglePredictRequest):
    """
    Prediksi sentimen untuk single text menggunakan metode lexicon.
    
    - **text**: Text untuk dianalisis
    
    Returns prediction dengan label, score, tokens, dan matched words.
    """
    try:
        output = predict_sentiment_lexicon_single(payload.text)
        return LexiconSinglePredictResponse(
            text=payload.text,
            label=LexiconSentimentLabel(output["label"]),
            score=output["score"],
            tokens=output["tokens"],
            matched_words=output["matched_words"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/analyze-post/{post_id}", response_model=LexiconAnalyzePostResponse)
def analyze_post_comments(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze sentiment untuk SEMUA komentar pada satu post menggunakan metode lexicon.
    
    Endpoint ini akan:
    1. Mengambil semua komentar dari post
    2. Melakukan prediksi sentiment menggunakan Lexicon
    3. Menyimpan hasil sentiment ke database
    4. Mengembalikan summary hasil analisis
    
    - **post_id**: ID post yang komentarnya akan dianalisis
    """
    # 1. Validasi post exists dan user punya akses
    db_post = ig_post_service.get_post_by_id(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram post not found"
        )
    
    db_account = ig_account_service.get_account_by_id(db, account_id=db_post.instagram_account_id)
    if db_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze this post's comments"
        )
    
    # 2. Ambil semua komentar dari post
    comments = ig_comment_service.get_comments_by_post(db, post_id=post_id, skip=0, limit=10000)
    
    if not comments:
        return LexiconAnalyzePostResponse(
            success=True,
            post_id=post_id,
            total_comments=0,
            analyzed_count=0,
            results=[],
            summary={"Positif": 0, "Negatif": 0, "Netral": 0},
            message="No comments found for this post"
        )
    
    # 3. Extract texts dan predict batch
    texts = [c.text for c in comments]
    
    try:
        predictions = predict_sentiment_lexicon(texts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment prediction failed: {str(e)}"
        )
    
    # 4. Update setiap komentar dengan hasil sentiment
    results: List[LexiconCommentResult] = []
    summary = {"Positif": 0, "Negatif": 0, "Netral": 0}
    
    for comment, pred in zip(comments, predictions):
        lexicon_label = pred["label"]  # "Positif", "Negatif", "Netral"
        db_label = LEXICON_TO_DB_LABEL.get(lexicon_label)
        score = pred["score"]
        
        # Update comment di database
        comment.sentiment_label = db_label
        comment.sentiment_score = score
        db.add(comment)
        
        # Track summary
        summary[lexicon_label] = summary.get(lexicon_label, 0) + 1
        
        # Build result
        results.append(LexiconCommentResult(
            comment_id=comment.id,
            text=comment.text[:100] + "..." if len(comment.text) > 100 else comment.text,
            label=LexiconSentimentLabel(lexicon_label),
            score=score,
            tokens=pred["tokens"]
        ))
    
    # 5. Commit semua perubahan
    db.commit()
    
    return LexiconAnalyzePostResponse(
        success=True,
        post_id=post_id,
        total_comments=len(comments),
        analyzed_count=len(results),
        results=results,
        summary=summary,
        message=f"Successfully analyzed {len(results)} comments using Lexicon method"
    )
