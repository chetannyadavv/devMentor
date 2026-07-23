import uuid

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Table, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


problem_topics = Table(
    "problem_topics",
    Base.metadata,
    Column("problem_id", UUID(as_uuid=True), ForeignKey("problems.id"), primary_key=True),
    Column("topic_id", UUID(as_uuid=True), ForeignKey("topics.id"), primary_key=True),
)

contest_problems = Table(
    "contest_problems",
    Base.metadata,
    Column("contest_id", UUID(as_uuid=True), ForeignKey("contests.id"), primary_key=True),
    Column("problem_id", UUID(as_uuid=True), ForeignKey("problems.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submissions = relationship("Submission", back_populates="user")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    statement = Column(Text, nullable=False)
    # Bumped whenever test cases change in a way that affects grading.
    # Submissions snapshot this value at submit time (see Submission
    # below) so a submission's grading context is always knowable, even
    # after the problem itself moves on to a later version.
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    topics = relationship("Topic", secondary=problem_topics, back_populates="problems")
    submissions = relationship("Submission", back_populates="problem")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False)
    stdin = Column(Text, nullable=False, default="")
    expected_output = Column(Text, nullable=False)
    # Sample cases are shown to the user on the problem page; non-sample
    # (hidden) cases are used for grading but not displayed.
    is_sample = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    problem = relationship("Problem", back_populates="test_cases")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)

    problems = relationship("Problem", secondary=problem_topics, back_populates="topics")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False)
    problem_version = Column(Integer, nullable=False)  # snapshot at submit time
    language = Column(String(20), nullable=False)
    source_code = Column(Text, nullable=False)
    overall_verdict = Column(String(30), nullable=True)  # null until judged
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")


class Contest(Base):
    __tablename__ = "contests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    problems = relationship("Problem", secondary=contest_problems)


class TestCaseResult(Base):
    __tablename__ = "test_case_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    test_case_index = Column(Integer, nullable=False)
    verdict = Column(String(30), nullable=False)
    stdout = Column(Text)
    stderr = Column(Text)
    exit_code = Column(Integer)
    runtime_seconds = Column(Float)
    timed_out = Column(Boolean, nullable=False, default=False)
    compile_error = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("Submission")
