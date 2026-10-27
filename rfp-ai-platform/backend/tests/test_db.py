from sqlalchemy import text
from app.db.session import SessionLocal

def test_db_connection():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1
    finally:
        db.close()
