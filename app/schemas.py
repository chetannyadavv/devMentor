import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProblemCreate(BaseModel):
    slug: str
    title: str
    statement: str


class ProblemUpdate(BaseModel):
    title: str | None = None
    statement: str | None = None


class ProblemOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    statement: str
    version: int

    class Config:
        from_attributes = True


class TestCaseCreate(BaseModel):
    stdin: str = ""
    expected_output: str
    is_sample: bool = False


class TestCaseOut(BaseModel):
    id: uuid.UUID
    stdin: str
    expected_output: str
    is_sample: bool

    class Config:
        from_attributes = True


class ProblemDetail(ProblemOut):
    sample_test_cases: list[TestCaseOut] = []


class ContestCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    problem_slugs: list[str] = []


class ContestOut(BaseModel):
    id: uuid.UUID
    title: str
    start_time: datetime
    end_time: datetime
    status: str  # "upcoming" | "active" | "ended" -- computed, not stored


class ContestProblemOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str


class ContestDetail(ContestOut):
    problems: list[ContestProblemOut] = []


class SubmissionCreate(BaseModel):
    problem_slug: str
    language: str
    source_code: str


class SubmissionOut(BaseModel):
    id: uuid.UUID
    problem_id: uuid.UUID
    language: str
    overall_verdict: str | None
    problem_version: int

    class Config:
        from_attributes = True


class ProblemCreate(BaseModel):
    slug: str
    title: str
    statement: str


class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    statement: Optional[str] = None


class ProblemListOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    version: int

    class Config:
        from_attributes = True


class ProblemOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    statement: str
    version: int

    class Config:
        from_attributes = True


class TestCaseCreate(BaseModel):
    stdin: str = ""
    expected_output: str
    is_sample: bool = False


class TestCaseOut(BaseModel):
    id: uuid.UUID
    problem_id: uuid.UUID
    stdin: str
    expected_output: str
    is_sample: bool

    class Config:
        from_attributes = True
