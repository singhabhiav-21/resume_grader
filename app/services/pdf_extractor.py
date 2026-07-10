import pymupdf4llm
import re
import os
from dotenv import load_dotenv

load_dotenv()

HEADER_PATTERNS = {
    "education": r"education|academic background",
    "skills": r"skills|technical skills|core competencies",
    "experience": r"experience|work experience|professional experience|employment history",
    "projects": r"projects|personal projects|key projects",
}

HEADER_LINE_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def convert_pdf_to_markdown(filepath, job_id, md_path=f"{os.getenv('FILE_PATH')}"):
    md = pymupdf4llm.to_markdown(filepath)
    file_name = filepath.split("/")[-1]
    print(file_name)
    md_path += str(job_id) + file_name + ".md"
    print(md_path)
    try:
        with open(md_path, "x") as file:
            file.write(md)
    except FileExistsError:
        raise FileExistsError("File already exists!")
    return md


def classify_headers(header_text: str):
    text = header_text.lower().strip()
    for label, pattern in HEADER_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


def split_markdown_to_chunks(md):
    findings = list(re.finditer(HEADER_LINE_RE, md))
    if not findings:
        return {"unnamed": md.strip()}

    chunks = {}

    first_intro = None
    for m in findings:
        if classify_headers(m.group(2)) is not None:
            first_intro = m
            break

    if first_intro is None:
        return {"unlabeled": md.strip()}

    chunks["intro"] = md[:first_intro.start()].strip()

    main_finds = [m for m in findings if classify_headers(m.group(2)) is not None]

    for i, m in enumerate(main_finds):
        label = classify_headers(m.group(2))
        start = m.end()
        if i + 1 < len(main_finds):
            end = main_finds[i + 1].start()
        else:
            end = len(md)
        body = md[start:end].strip()

        if label in chunks:
            chunks[label] = chunks[label] + "\n" + body
        else:
            chunks[label] = body

    return chunks


def chunk_for_embedding(chunk, limit=1500):
    out = {}
    for label, text in chunk.items():
        if isinstance(text, list):
            out[label] = [text]
            continue
        if len(text) < limit:
            out[label] = [text]
            continue
        raw_para = text.split("\n\n")
        merge = []
        buffer = ""
        for para in raw_para:
            para = para.strip()
            if not para:
                continue
            if len(para) + len(buffer) < limit:
                if buffer:
                    buffer = buffer + "\n\n" + para
                else:
                    buffer = para
            else:
                if buffer:
                    merge.append(buffer)
                buffer = para
        if buffer:
            merge.append(buffer)
        out[label] = merge
    return out


def prepare_to_embed(chunks: dict):
    ready = []
    for category, chunk in chunks.items():
        if category == "intro":
            continue
        for i, text in enumerate(chunk):
            ready.append({
                "id": f"{category}_{i}",
                "text": f"{text}",
                "category": f"{category}"
            })

    return ready
