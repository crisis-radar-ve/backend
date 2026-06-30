from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reviewer
from app.services.auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    reviewer: dict


@router.post("/login", response_model=TokenOut)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    reviewer = db.query(Reviewer).filter(Reviewer.email == payload.email).first()
    if not reviewer or not reviewer.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, reviewer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not reviewer.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    token = create_access_token({"sub": str(reviewer.id), "role": reviewer.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "reviewer": {
            "id": str(reviewer.id),
            "name": reviewer.name,
            "email": reviewer.email,
            "role": reviewer.role,
        },
    }
