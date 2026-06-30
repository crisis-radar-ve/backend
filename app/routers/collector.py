from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reviewer
from app.services.auth import get_current_reviewer
from app.services.collector import collect_rss_feeds, collect_google_news

router = APIRouter(prefix="/collect", tags=["collector"])


class CollectQuery(BaseModel):
    query: str


@router.post("/rss")
def collect_rss(
    db: Session = Depends(get_db),
    reviewer: Reviewer = Depends(get_current_reviewer),
):
    result = collect_rss_feeds(db)
    return result


@router.post("/google-news")
def collect_google_news_route(
    payload: CollectQuery,
    db: Session = Depends(get_db),
    reviewer: Reviewer = Depends(get_current_reviewer),
):
    result = collect_google_news(db, payload.query)
    return result
