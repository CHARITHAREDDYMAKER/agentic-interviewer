import os
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from typing import Optional, List

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API")

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    work_mode: str

    salary_range: Optional[str] = None

    experience_required: str
    job_type: str

    description: str

    required_skills: List[str]
    missing_skills: List[str]

    match_score: float
    match_reason: str

    apply_link: str
    source: str   # IMPORTANT: "lever", "greenhouse", "remotive"


class JobRecommendations(BaseModel):
    jobs: list[JobListing]
    search_tips: list[str]      # 2-3 job-hunt tips specific to the candidate



from pydantic_ai.providers.google_gla import GoogleGLAProvider
model = GeminiModel("gemini-3-flash-preview", provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))

job_agent = Agent(
    model=model,
    output_type=JobRecommendations,
    system_prompt="""You are a career advisor and talent marketplace specialist.
Generate realistic job recommendations for a candidate based on their profile.

Rules:
- Generate exactly 6 job listings
- Mix seniority levels: 2 stretch roles, 3 good-fit roles, 1 safe/entry-level role
- Use realistic companies (mix of product companies, startups, MNCs)
- Include Indian salary ranges if location seems India-based, else USD
- missing_skills should be honest — what they actually lack for that role
- match_score: realistic (60-95 range for recommended jobs)
- Vary work_mode across the 6 listings
- search_tips: actionable advice specific to their background
""",
)


async def get_job_recommendations(
    skills: list[str],
    roles: list[str],
    experience_years: int,
    resume_summary: str,
) -> dict:
    prompt = f"""Candidate profile:
Summary: {resume_summary}
Skills: {', '.join(skills)}
Target roles: {', '.join(roles)}
Experience: {experience_years} years

Generate 6 relevant job recommendations."""

    result = await job_agent.run(prompt)
    data = result.output
    return {
        "jobs": [j.model_dump() for j in data.jobs],
        "search_tips": data.search_tips,
    }