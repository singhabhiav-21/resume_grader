from google import genai
from google.genai import types
from google.genai.errors import APIError
import json

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

Overall Assessment
Summarize how well the resume matches the role, based only on the
covered/partial/gap data above, and note whether the resume text overall
leans toward vague responsibility statements or concrete, measurable
achievements.

Strong Matches
List requirements the candidate demonstrates. For each one, name the
requirement, then quote the specific resume phrase that supports it.

Missing or Weak Areas
List requirements marked as GAP or PARTIAL. For each one, name the
requirement and state plainly what specific evidence is absent — not
just "not demonstrated" in general terms.

Resume Language & Impact
Based only on the resume text shown above, note where the candidate uses
strong action verbs and quantifiable results (numbers, percentages,
scale) versus where bullets are vague or purely descriptive. Flag any
requirement area where the resume lists a tool or skill by name only,
with no supporting result or outcome attached — this is the kind of
phrasing a recruiter or applicant tracking keyword scan would treat as
weak signal even if the keyword itself is present.

Resume Improvements
Suggest how the candidate could better *phrase or surface* existing
experience to address weak areas — do not suggest they add experience
they don't have.

Interview Risk Areas
If both the GAP entries and the PARTIAL entries are empty above, write:
"No significant risk areas identified — the resume shows strong alignment
with this role's core requirements."
Otherwise, base this section on entries marked GAP above, plus any
PARTIAL entries where an interviewer would likely probe further because
a tool or practice is listed but not demonstrated with specifics. Do not
include a PARTIAL entry here if its "Missing or Weak Areas" treatment
already covers it adequately — only surface the ones most likely to come
up as a follow-up question.
"""


def llm_feedback(prompt, job_id, user_id):
    client = genai.Client()
    try:
        for chunk in client.models.generate_content_stream(
                model="gemini-3.5-flash",
                contents=prompt):
            if chunk.text:
                yield f"data: {json.dumps(chunk.text)}\n\n"
        update_job(job_id, user_id, "Completed")
    except APIError as e:
        update_job(job_id, user_id, "Failed")
        yield f"event: error\ndata: {str(e)}\n\n"
