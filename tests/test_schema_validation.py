import pytest

from resume_compiler.domain.schema import Resume


def test_resume_schema_valid_minimal(tmp_path):
    payload = {
        "contact": {"name": "Test User", "email": "test@example.com"},
        "summary": "Hello",
        "experience": [],
        "skills": [],
    }
    Resume.model_validate(payload)


def test_resume_schema_invalid_email():
    payload = {"contact": {"name": "Test", "email": "not-an-email"}}
    with pytest.raises(Exception):
        Resume.model_validate(payload)
