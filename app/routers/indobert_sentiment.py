"""
IndoBERT Sentiment Analysis Router

Endpoints untuk analisis sentimen menggunakan model IndoBERT fine-tuned.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.dependencies import get_db, get_current_active_user
from app.schemas.indobert import (
    IndoBertPredictRequest,
    IndoBertPredictResponse,
    IndoBertSinglePredictRequest,
    IndoBertSinglePredictResponse,
    IndoBertPrediction,
    SentimentLabel,
    AnalyzePostCommentsResponse,
    CommentSentimentResult,
)
from app.services.indobert_service import (
    predict_sentiment,
    predict_sentiment_single,
    get_indobert_model,
)
from app.services import ig_comment_service, ig_post_service, ig_account_service
from app.models.user import User
from app.models.enums import SentimentLabel as DBSentimentLabel


# Mapping dari IndoBERT label ke database enum
INDOBERT_TO_DB_LABEL = {
    "Positif": DBSentimentLabel.POSITIVE,
    "Negatif": DBSentimentLabel.NEGATIVE,
    "Netral": DBSentimentLabel.NEUTRAL,
}


router = APIRouter(prefix="/indobert", tags=["IndoBERT Sentiment"])


@router.get("/health")
def health_check():
    """Check if the IndoBERT model is loaded and ready."""
    try:
        model = get_indobert_model()
        return {
            "status": "healthy",
            "model_loaded": True,
            "num_labels": model.num_labels,
            "labels": list(model.id2label.values())
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")


@router.post("/predict", response_model=IndoBertPredictResponse)
def predict_batch(payload: IndoBertPredictRequest):
    """
    Prediksi sentimen untuk multiple texts (batch).
    
    - **texts**: List of texts untuk dianalisis
    
    Returns predictions dengan label (Negatif/Netral/Positif) dan confidence score.
    """
    try:
        outputs = predict_sentiment(payload.texts)
        predictions = [
            IndoBertPrediction(
                label=SentimentLabel(o["label"]),
                score=o["score"],
                scores=o["scores"]
            )
            for o in outputs
        ]
        return IndoBertPredictResponse(predictions=predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/single", response_model=IndoBertSinglePredictResponse)
def predict_single(payload: IndoBertSinglePredictRequest):
    """
    Prediksi sentimen untuk single text.
    
    - **text**: Text untuk dianalisis
    
    Returns prediction dengan label, score, dan scores untuk semua label.
    """
    try:
        output = predict_sentiment_single(payload.text)
        return IndoBertSinglePredictResponse(
            text=payload.text,
            label=SentimentLabel(output["label"]),
            score=output["score"],
            scores=output["scores"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/analyze-post/{post_id}", response_model=AnalyzePostCommentsResponse)
def analyze_post_comments(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze sentiment untuk SEMUA komentar pada satu post.
    
    Endpoint ini akan:
    1. Mengambil semua komentar dari post
    2. Melakukan prediksi sentiment menggunakan IndoBERT
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
    
    # 2. Ambil semua komentar dari post (tanpa limit)
    comments = ig_comment_service.get_comments_by_post(db, post_id=post_id, skip=0, limit=10000)
    
    if not comments:
        return AnalyzePostCommentsResponse(
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
        predictions = predict_sentiment(texts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment prediction failed: {str(e)}"
        )
    
    # 4. Update setiap komentar dengan hasil sentiment
    results: List[CommentSentimentResult] = []
    summary = {"Positif": 0, "Negatif": 0, "Netral": 0}
    
    for comment, pred in zip(comments, predictions):
        indobert_label = pred["label"]  # "Positif", "Negatif", "Netral"
        db_label = INDOBERT_TO_DB_LABEL.get(indobert_label)
        score = pred["score"]
        
        # Update comment di database
        comment.sentiment_label = db_label
        comment.sentiment_score = score
        db.add(comment)
        
        # Track summary
        summary[indobert_label] = summary.get(indobert_label, 0) + 1
        
        # Build result
        results.append(CommentSentimentResult(
            comment_id=comment.id,
            text=comment.text[:100] + "..." if len(comment.text) > 100 else comment.text,
            label=SentimentLabel(indobert_label),
            score=score,
            scores=pred["scores"]
        ))
    
    # 5. Commit semua perubahan
    db.commit()
    
    return AnalyzePostCommentsResponse(
        success=True,
        post_id=post_id,
        total_comments=len(comments),
        analyzed_count=len(results),
        results=results,
        summary=summary,
        message=f"Successfully analyzed {len(results)} comments"
    )
