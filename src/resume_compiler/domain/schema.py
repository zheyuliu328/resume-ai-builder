from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class Period(BaseModel):
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$")
    current: bool = False


class ExperienceItem(BaseModel):
    company: str
    position: str
    location: str = ""
    period: Period

    # 原始输入：用户草稿
    raw_highlights: list[str]

    # AI 生成后的结果，生成前为空
    refined_highlights: Optional[list[str]] = None

    tech_stack: list[str] = Field(default_factory=list)


class ResumeContext(BaseModel):
    """用于控制生成风格的上下文。"""

    target_role: str
    language: Literal["en_US", "zh_CN"] = "en_US"
    tone: Literal["professional", "academic", "creative"] = "professional"
    constraints: dict = Field(default_factory=lambda: {"max_pages": 1})


class Contact(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None


class Resume(BaseModel):
    contact: Contact
    summary: Optional[str] = None
    experience: list[ExperienceItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
