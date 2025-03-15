from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user_optional
from app.db.session import get_db
from app.db.models import User
from app.services.content_generator import generate_educational_content
from app.api.base_dependencies import verify_csrf_token

router = APIRouter()


class ContentPreviewRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "medium"  # easy, medium, hard


@router.post("/generate", response_class=HTMLResponse, dependencies=[Depends(verify_csrf_token)])
async def generate_content_preview(
    request: ContentPreviewRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Generate a preview of educational content for a specific topic
    """
    # Validate difficulty level
    if request.difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Difficulty must be 'easy', 'medium', or 'hard'",
        )
    
    # Generate preview content
    content = await generate_educational_content(
        topic=request.topic,
        is_preview=True,
        difficulty=request.difficulty
    )
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview content",
        )
    
    # Wrap content in a styled container
    styled_content = f"""
    <div class="content-preview-container" style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="padding: 20px;">
            {content}
        </div>
    </div>
    """
    
    return HTMLResponse(content=styled_content)