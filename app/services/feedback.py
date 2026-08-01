from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import HTTPException

from app.services.job_to_user import update_job


def get_results_feedback(chunks):
    prompt_details = []
    for cat, status in chunks.items():
        for some, gaps in status.items():
            for i, gap in enumerate(gaps, start=1):
                prompt_details.append(f""" Requirement {i}:
- Job Requirement: {gap["jd_text"]}
- Resume Section: {gap["resume_section"]}
- Resume Text: {gap["resume_text"]}
- Match Score: {gap["distance"]}
- Category: {cat}
- Gap: {some}
""")
    return "\n".join(prompt_details)


def build_prompt(details):
    return f"""You are a technical recruiter reviewing a resume against a job description.

Below is structured matching data: each job requirement, the closest
matching resume text found for it, and a similarity score (0 to 1, higher
is stronger evidence).

{details}

STRICT RULES — follow exactly:
- Base every claim ONLY on the text provided above. Do not infer, assume,
  or invent skills, tools, years of experience, or achievements that are
  not explicitly present in the "Closest resume evidence" text.
- For items marked GAP, the resume text shown is the closest available
  match, not actual supporting evidence — treat these as genuinely
  unaddressed by the resume, not as a weak match.
- If there isn't enough information in the data above to say something
  meaningful for a section below, write "Not enough information in the
  resume to assess this" instead of guessing.
- Do not restate the raw similarity scores in your answer — use them only
  to judge confidence internally.
- Quote or closely paraphrase the actual resume text when citing a
  strength; do not describe skills in more impressive terms than the
  original text supports.
- Write in plain text only. Do not use markdown — no #, ##, *, **, -, or
  any other markdown syntax. Section titles should be plain text on their
  own line, followed by a colon.

Provide feedback in this structure:

Overall Assessment
Summarize how well the resume matches the role, based only on the
covered/partial/gap data above.

Strong Matches
List requirements the candidate demonstrates, citing the specific resume
text that supports each one.

Missing or Weak Areas
List requirements marked as GAP or PARTIAL, and say plainly that the
resume does not currently demonstrate them.

Resume Improvements
Suggest how the candidate could better *phrase or surface* existing
experience to address weak areas — do not suggest they add experience
they don't have.

Interview Risk Areas
If the GAP data is empty for both requirements and optional, write:
"No significant risk areas identified — the resume shows strong alignment
with this role's core requirements."
Otherwise, base this section only on entries actually marked GAP above.
"""


def llm_feedback(prompt, job_id, user_id):
    client = genai.Client()
    try:
        for chunk in client.models.generate_content_stream(
                model="gemini-3.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(thinking_level="medium")):
            if chunk.text:
                yield f"data: {chunk.text}\n\n"
        update_job(job_id, user_id, "Completed")
    except APIError as e:
        update_job(job_id, user_id, "Failed")
        yield f"event: error\ndata: {str(e)}\n\n"
