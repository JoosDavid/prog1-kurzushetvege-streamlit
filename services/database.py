
from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    event
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)

# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_DIR = PROJECT_ROOT / "database"
DB_PATH = DB_DIR / "quiz_results.db"

# Ensure database directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# DATABASE ENGINE
# =========================================================

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={
        "timeout": 30,
        "check_same_thread": False
    }
)


# =========================================================
# SQLITE CONFIGURATION
# =========================================================

@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection, connection_record):

    cursor = dbapi_connection.cursor()

    # Better concurrent read/write behavior
    cursor.execute("PRAGMA journal_mode=WAL")

    # Wait up to 30 seconds if database is locked
    cursor.execute("PRAGMA busy_timeout=30000")

    cursor.close()


# =========================================================
# ORM
# =========================================================

Base = declarative_base()

Session = sessionmaker(
    bind=engine,
    expire_on_commit=False
)


class QuizResult(Base):

    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(String, nullable=False, index=True)

    score = Column(Integer, nullable=False)

    total = Column(Integer, nullable=False)


# Create tables if they do not exist
Base.metadata.create_all(engine)


# =========================================================
# SAVE RESULT
# =========================================================

def save_result(username, score, total):

    with Session() as session:

        result = QuizResult(
            username=username,
            score=score,
            total=total
        )

        session.add(result)
        session.commit()

        return result.id


# =========================================================
# FETCH RESULTS
# =========================================================

def fetch_results():

    with Session() as session:

        results = (
            session.query(QuizResult)
            .order_by(QuizResult.score.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "username": r.username,
                "score": r.score,
                "total": r.total
            }
            for r in results
        ]
