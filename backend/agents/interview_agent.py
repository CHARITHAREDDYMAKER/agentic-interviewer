import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# ── Load .env ─────────────────────────────────────────────────────────────────
_this_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=_this_dir / ".env", override=True)
load_dotenv(dotenv_path=_this_dir.parent / ".env", override=False)
load_dotenv(dotenv_path=_this_dir.parent.parent / ".env", override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API") or os.getenv("GEMINI_API_KEY")
print(f"[interview_agent] Key loaded: {'YES' if GEMINI_API_KEY else 'NO — add GEMINI_API to .env'}")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL  = "gemini-2.0-flash"       # correct name for google-genai SDK
TOTAL_QUESTIONS = 10

# ── helpers ───────────────────────────────────────────────────────────────────
def parse_json(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            p = part.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            try:
                return json.loads(p)
            except Exception:
                continue
    return json.loads(text)

async def call_gemini(prompt: str, max_retries: int = 4) -> str:
    delays = [15, 30, 60, 90]
    loop   = asyncio.get_event_loop()
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                )
            )
            return resp.text
        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["quota", "429", "resource_exhausted", "rate", "exhausted"]):
                if attempt < max_retries - 1:
                    d = delays[attempt]
                    print(f"[Gemini] Rate limit hit. Waiting {d}s... (attempt {attempt+1})")
                    await asyncio.sleep(d)
                    last_err = e
                    continue
            raise Exception(f"Gemini error: {e}")
    raise Exception(f"Rate limit after {max_retries} retries. Wait ~1 min. Error: {last_err}")

# ── start_interview ───────────────────────────────────────────────────────────
async def start_interview(role: str, resume_summary: str, skills: list, experience_years: int) -> dict:
    prompt = f"""You are a senior interviewer. Return ONLY valid JSON with no markdown fences.

Role: {role}
Background: {resume_summary}
Skills: {', '.join(skills)}
Experience: {experience_years} years

Generate a warm-up behavioral first question for this specific role.

Return exactly this JSON:
{{
  "question": "your question here",
  "question_type": "behavioral",
  "hint": "one sentence tip",
  "difficulty": "warm-up",
  "topic": "topic name"
}}"""

    text = await call_gemini(prompt)
    try:
        data = parse_json(text)
    except Exception:
        data = {}
    return {
        "question":        data.get("question", f"Tell me about yourself and why you are interested in the {role} role."),
        "question_type":   "behavioral",
        "hint":            data.get("hint", "Use the STAR method."),
        "difficulty":      "warm-up",
        "topic":           data.get("topic", "introduction"),
        "question_number": 1,
        "total_questions": TOTAL_QUESTIONS,
    }

# ── next_question ─────────────────────────────────────────────────────────────
async def next_question(role: str, resume_summary: str, question: str,
                        answer: str, history: list, question_number: int) -> dict:
    history_lines, used_topics = [], []
    for i, h in enumerate(history):
        t = h.get("topic", f"topic_{i}")
        used_topics.append(t)
        history_lines.append(
            f"Q{i+1}[{h.get('question_type','?')}] topic={t}: {h['question']}\n"
            f"  Answer: {h['answer']}\n  Score: {h.get('score','?')}/10"
        )

    recent = [h.get("score", 5) for h in history[-3:]]
    avg    = sum(recent) / len(recent) if recent else 5
    trend  = ("Drop difficulty — candidate struggling." if avg <= 4
              else "Increase difficulty — candidate excelling." if avg >= 8
              else "Maintain difficulty.")

    is_final = question_number >= TOTAL_QUESTIONS

    prompt = f"""You are a senior interviewer for {role}. Return ONLY valid JSON with no markdown fences.

Candidate background: {resume_summary}

History (FORBIDDEN topics — never repeat: {', '.join(used_topics) or 'none'}):
{chr(10).join(history_lines) or 'No previous questions.'}

Current Q{question_number}/{TOTAL_QUESTIONS}: {question}
Candidate answer: {answer}

Adaptive rule: {trend}
Progression: Q1-2=warm-up behavioral, Q3-5=mid technical, Q6-8=tough technical, Q9-10=edge cases.
is_final = {"true" if is_final else "false"}

Return exactly this JSON:
{{
  "score": 7,
  "feedback": "2-3 sentence coaching note",
  "is_final": {"true" if is_final else "false"},
  "next_question": {{
    "question": "next role-specific question on a NEW topic",
    "question_type": "technical",
    "hint": "one sentence tip",
    "difficulty": "mid",
    "topic": "new unique topic"
  }}
}}"""

    text = await call_gemini(prompt)
    try:
        data = parse_json(text)
    except Exception:
        data = {}

    response = {
        "score":    int(data.get("score", 5)),
        "feedback": data.get("feedback", "Good attempt. Try using specific examples next time."),
        "is_final": bool(data.get("is_final", is_final)),
    }
    nq = data.get("next_question", {})
    if not response["is_final"] and nq:
        response["next_question"] = {
            "question":        nq.get("question", f"Describe a challenging problem you solved as a {role}."),
            "question_type":   nq.get("question_type", "technical"),
            "hint":            nq.get("hint", "Be specific."),
            "difficulty":      nq.get("difficulty", "mid"),
            "topic":           nq.get("topic", f"topic_{question_number}"),
            "question_number": question_number + 1,
            "total_questions": TOTAL_QUESTIONS,
        }
    return response

# ── get_feedback ──────────────────────────────────────────────────────────────
async def get_feedback(role: str, history: list) -> dict:
    history_text = "\n\n".join(
        [f"Q{i+1}[{h.get('question_type','?')}]: {h['question']}\n"
         f"Answer: {h['answer']}\nScore: {h.get('score','?')}/10"
         for i, h in enumerate(history)]
    )
    prompt = f"""You are a senior hiring manager. Return ONLY valid JSON with no markdown fences.

Role: {role}
Transcript:
{history_text}

Return exactly this JSON:
{{
  "overall_score": 72,
  "overall_verdict": "Hire",
  "summary": "2-3 sentence summary",
  "strengths": ["s1", "s2", "s3"],
  "areas_to_improve": ["a1", "a2", "a3"],
  "per_question_scores": [{{"question": "...", "score": 7, "note": "..."}}],
  "recommended_resources": ["resource1", "resource2"]
}}
Verdict: Strong Hire(85+), Hire(70-84), Borderline(50-69), No Hire(<50)"""

    text = await call_gemini(prompt, max_retries=4)
    try:
        data = parse_json(text)
    except Exception:
        data = {}
    return {
        "overall_score":         int(data.get("overall_score", 60)),
        "overall_verdict":       data.get("overall_verdict", "Borderline"),
        "summary":               data.get("summary", "Interview completed."),
        "strengths":             data.get("strengths", []),
        "areas_to_improve":      data.get("areas_to_improve", []),
        "per_question_scores":   data.get("per_question_scores", []),
        "recommended_resources": data.get("recommended_resources", []),
    }