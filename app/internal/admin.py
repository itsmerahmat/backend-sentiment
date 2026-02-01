from fastapi import APIRouter, Depends

from app.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
def get_admin_dashboard(current_user: User = Depends(get_current_active_user)):
    """Admin dashboard endpoint."""
    return {
        "message": "Admin Dashboard",
        "user": current_user.username
    }


@router.get("/stats")
def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get application statistics."""
    return {
        "message": "Application Statistics",
        "stats": {
            "users": 0,
            "items": 0
        }
    }
