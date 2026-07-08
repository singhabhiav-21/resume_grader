import re
from dotenv import load_dotenv

load_dotenv()

TITLES_PATTERN = {
    "requirements": r"requirements|qualifications|required qualifications|minimum qualifications|what you'll "
                    r"need|what you need|must haves|skills & requirements|basic qualifications|what we're looking "
                    r"for|who you are|experience required",
    "optional": r"additional qualifications|bonus points|bonus skills|desired skills|extra credit|good to have|nice "
                r"to have|pluses|preferred qualifications|preferred skills|what would be great",
    "responsibilities": r"core responsibilities|day-to-day|duties|job duties|key "
                        r"responsibilities|responsibilities|the impact you'll have|the role|what you'll be doing|what "
                        r"you'll do|your role|accountabilities"
}

IGNORE_PATTERN = (
    r"benefits|perks|how (?:it|jobgether) works|why apply|"
    r"data privacy notice|about\s+\w+|equal opportunity|"
    r"practical details|why this role|the team"
)


def classifying_headers(line):
    clean_line = line.strip()
    if not clean_line:
        return None, None

    bare = clean_line.lower().rstrip(":")
    if len(bare.split()) <= 6:
        for category, pattern in TITLES_PATTERN.items():
            if re.fullmatch(pattern, bare):
                return category, ""

    if re.match(rf"^(?:{IGNORE_PATTERN})\b", bare):
        return "__ignore__", ""

    for category, pattern in TITLES_PATTERN.items():
        m = re.match(rf"^(?:{pattern})\s*[:\-]\s*(.+)$", clean_line, re.IGNORECASE)
        if m:
            return category, m.group(1).strip()
        n = re.match(rf"^(?:{IGNORE_PATTERN})\s*[:\-]\s*(.+)$", clean_line, re.IGNORECASE)
        if n:
            return "__ignore__", n.group(1).strip()
    return None, None


def split_header(texts: str):
    lines = texts.splitlines()

    headers = []
    for i, line in enumerate(lines):
        category, trail = classifying_headers(line)
        if category is not None:
            headers.append((i, category, trail))

    if not headers:
        return {"unlabeled_text": texts.strip()}

    sections = {}
    first = headers[0][0]
    sections["intro"] = "\n".join(lines[:first]).lower().strip()

    for i, (lines_idx, category, trail) in enumerate(headers):
        start = lines_idx + 1
        if i + 1 < len(headers):
            end = headers[i + 1][0]
        else:
            end = len(lines)
        body = "\n".join(lines[start:end]).lower().strip()

        if trail:
            body = (trail + "\n" + body).strip() if body else trail

        if category in sections:
            sections[category] = sections[category] + "\n" + body
        else:
            sections[category] = "\n" + body
    sections.pop("__ignore__", None)
    sections.pop("intro", None)
    return sections


def chunk_to_embed(chunks: dict):
    final = {}
    for category, text in chunks.items():
        bullet = [line.strip() for line in text.split("\n") if line.strip()]
        final[category] = bullet
    return final


def proper_meta_data(chunks: dict):
    flattened = []
    for category, chunks in chunks.items():
        for i, chunk_text in enumerate(chunks):
            flattened.append({
                "id": f"{category}_{i}",
                "text": chunk_text,
                "category": category,
            })
    return flattened


def ready_to_embed(filename):
    document = f"/app/services/jd_test.txt"

    with open(document) as f:
        jd = f.read()  # print(text_splitter.split_text(jd))

    header = split_header(jd)
    final = chunk_to_embed(header)
    return proper_meta_data(final)


