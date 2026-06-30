"""Seed initial admin user."""

from app.database import SessionLocal, Base, engine
from app.models import Reviewer
from app.services.auth import hash_password


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Reviewer).filter(Reviewer.email == "frankponte95@gmail.com").first()
        if existing:
            print("User already exists")
            return

        reviewer = Reviewer(
            name="Frank Ponte",
            email="frankponte95@gmail.com",
            role="admin",
            organization="Crisis Radar VE",
            password_hash=hash_password("crisiscaracas26"),
            active=True,
        )
        db.add(reviewer)
        db.commit()
        print("Created admin user frankponte95@gmail.com")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
