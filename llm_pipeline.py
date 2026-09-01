"""
llm_pipeline.py
----------------
LLM-assisted resume extraction and matching (Phase B of the project roadmap).

This module replaces the old fixed skill-list + TF-IDF approach with:
  1. extract_profile()   -> LLM reads raw resume text and returns a structured
                             JSON profile (name, email, education, experience,
                             skills, years of experience). Works for Thai and
                             English resumes without a hand-maintained skill list.
  2. evaluate_match()     -> LLM compares a candidate profile against a job
                             description and returns a score PLUS an
                             explanation (matched/missing skills, experience
                             gap, and a short natural-language "reasoning"
                             string) so results are explainable, not just a
                             number.

Design notes
------------
- Uses the official `anthropic` Python SDK. Requires an ANTHROPIC_API_KEY
  environment variable. If it is not set, `is_available()` returns False and
  app.py falls back to the legacy TF-IDF pipeline automatically.
- We ask the model for JSON only and parse it defensively (models sometimes
  wrap JSON in prose or code fences), so `_extract_json` strips those before
  `json.loads`.
- Kept dependency-light on purpose: no embedding model / vector DB is
  required, since a single well-structured LLM call already gives semantic
  matching + reasoning in one step. If you want a cheaper first pass at
  scale (hundreds of resumes), swap the matching call for local sentence
  embeddings and reserve the LLM call for the top-N candidates only.
"""

import os
import re
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("RESUME_ANALYZER_MODEL", "claude-sonnet-4-6")

_client = None


def is_available():
    """True if an API key is configured and the SDK is importable."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


def _extract_json(raw_text):
    """Pull a JSON object out of a model response, tolerating code fences
    or a short preamble/postamble the model may add despite instructions."""
    if not raw_text:
        raise ValueError("empty response from model")

    text = raw_text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences if present.
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to grabbing the outermost { ... } block.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


PROFILE_SCHEMA_HINT = """{
  "name": "string",
  "email": "string or null",
  "phone": "string or null",
  "education": [
    {"degree": "string", "field": "string", "institution": "string", "year": "string or null"}
  ],
  "experience": [
    {"title": "string", "company": "string", "duration": "string", "years": "number"}
  ],
  "total_years_experience": "number",
  "skills": ["string", "..."],
  "languages": ["string", "..."]
}"""


def extract_profile(resume_text, model=None):
    """Turn raw resume text (Thai and/or English, OCR or PDF-extracted) into
    a structured profile dict. Raises on API/parsing failure -- caller should
    catch and fall back to the legacy extractor for that resume."""
    client = _get_client()
    model = model or DEFAULT_MODEL

    system_prompt = (
        "You are a resume-parsing engine. You read resumes in Thai and/or "
        "English and output ONLY a single JSON object matching the given "
        "schema. No prose, no markdown fences, no explanations -- JSON only. "
        "If a field is not present in the resume, use null (or an empty "
        "list for list fields). Infer skills from context (e.g. a bullet "
        "describing work with 'Power BI dashboards' implies the skill "
        "'Power BI') rather than requiring an exact 'Skills:' section. "
        "Estimate total_years_experience from the listed experience entries."
    )
    user_prompt = (
        f"Schema:\n{PROFILE_SCHEMA_HINT}\n\n"
        f"Resume text:\n\"\"\"\n{resume_text[:12000]}\n\"\"\"\n\n"
        "Return the JSON object now."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    profile = _extract_json(raw)

    # Normalize/guard fields so downstream code never KeyErrors.
    profile.setdefault("name", None)
    profile.setdefault("email", None)
    profile.setdefault("phone", None)
    profile.setdefault("education", [])
    profile.setdefault("experience", [])
    profile.setdefault("total_years_experience", 0)
    profile.setdefault("skills", [])
    profile.setdefault("languages", [])
    return profile


EVALUATION_SCHEMA_HINT = """{
  "score": "integer 0-100",
  "matched_skills": ["string", "..."],
  "missing_skills": ["string", "..."],
  "experience_fit": "one short sentence",
  "education_fit": "one short sentence",
  "reasoning": "2-4 sentences explaining the score, in Thai"
}"""


def evaluate_match(profile, job_description, model=None):
    """Compare a structured candidate profile against a job description.
    Returns a score plus an explanation so results are auditable, not a
    black-box number. `reasoning` is written in Thai by default so it reads
    naturally for a Thai HR reviewer; pass a different instruction in
    job_description if you need another language."""
    client = _get_client()
    model = model or DEFAULT_MODEL

    system_prompt = (
        "You are a fair, consistent resume-screening assistant. Compare the "
        "candidate profile (JSON) against the job description and return "
        "ONLY a single JSON object matching the given schema -- no prose "
        "outside the JSON. Base the score only on job-relevant qualifications "
        "(skills, experience, education). Do NOT let the candidate's name, "
        "gender, age, or the prestige of their school influence the score -- "
        "judge substance only. missing_skills should list requirements from "
        "the job description the candidate's profile does not show evidence "
        "of."
    )
    user_prompt = (
        f"Schema:\n{EVALUATION_SCHEMA_HINT}\n\n"
        f"Candidate profile:\n{json.dumps(profile, ensure_ascii=False)}\n\n"
        f"Job description:\n\"\"\"\n{job_description}\n\"\"\"\n\n"
        "Return the JSON object now."
    )

    response = client.messages.create(
        model=model,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    evaluation = _extract_json(raw)

    evaluation.setdefault("score", 0)
    evaluation.setdefault("matched_skills", [])
    evaluation.setdefault("missing_skills", [])
    evaluation.setdefault("experience_fit", "")
    evaluation.setdefault("education_fit", "")
    evaluation.setdefault("reasoning", "")
    return evaluation
