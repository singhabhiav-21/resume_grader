import re

BLOCK_TEXT = [
    r"rm\s+-rf",
    r"curl\s+.*\|\s*(bash|sh)",
    r"wget\s+",
    r"\$\(.+\)",
    r"`.*`",
    r"<script",
    r"javascript:",
    r"eval\(",
    r"exec\(",
    r"ignore\s+previous\s+instructions",
    r"drop\s+table",
    r"union\s+select",
    r"\.\./",
]


def validate_jd(jd_text: str):
    cleaned = jd_text.lower()
    if len(cleaned) > 3000:
        raise ValueError("The text is too large!")
    for text in BLOCK_TEXT:
        if re.search(text, cleaned):
            raise ValueError("Suspicious Text Detected!")
    return jd_text


