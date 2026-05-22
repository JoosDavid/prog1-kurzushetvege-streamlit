from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)

Base = declarative_base()

engine = create_engine(
    "sqlite:///database/quiz_results.db"
)

Session = sessionmaker(bind=engine)


class QuizResult(Base):

    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True)

    username = Column(String)

    score = Column(Integer)

    total = Column(Integer)


Base.metadata.create_all(engine)


def save_result(username, score, total):

    session = Session()

    result = QuizResult(
        username=username,
        score=score,
        total=total
    )

    session.add(result)

    session.commit()

    session.close()


def fetch_results():

    session = Session()

    results = session.query(QuizResult).all()

    session.close()

    return results