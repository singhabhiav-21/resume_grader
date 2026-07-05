import pymupdf4llm
import re
import json


HEADER_PATTERNS = {
    "education": r"education|academic background",
    "skills": r"skills|technical skills|core competencies",
    "experience": r"experience|work experience|professional experience|employment history",
    "projects": r"projects|personal projects|key projects",
}

HEADER_LINE_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def convert_pdf_to_markdown(filename, md_path="/Users/abhinavsingh/resume-grader/app/disk_stor/extracter.md"):
    md = pymupdf4llm.to_markdown(filename)
    if md_path:
        with open(md_path, "w") as file:
            file.write(md)
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
    if chunks.get("intro"):
        for i, text in enumerate(chunks["intro"]):
            ready.append({"id": f"intro{i}", "text": text, "section": "intro"})
    if chunks.get("skills"):
        for i, text in enumerate(chunks["skills"]):
            ready.append({"id": f"skills_{i}", "text": text, "section": "skills"})
    if chunks.get("education"):
        for i, text in enumerate(chunks["education"]):
            ready.append({"id": f"education_{i}", "text": text, "section": "education" })
    if chunks.get("projects"):
        for i, text in enumerate(chunks["projects"]):
            ready.append({"id": f"projects_{i}", "text": text, "section": "projects"})
    if chunks.get("experience"):
        for i, text in enumerate(chunks["experience"]):
            ready.append({"id": f"experience_{i}", "text": text, "section": "experience"})

    return ready


def pdf_extractor(filename):
    md_text = convert_pdf_to_markdown(f"/Users/abhinavsingh/resume-grader/app/disk_stor/{filename}")
    print(f"Saved markdown to resume.md ({len(md_text)} chars)")

    chunks = split_markdown_to_chunks(md_text)
    chunked = chunk_for_embedding(chunks)
    ready = prepare_to_embed(chunked)
    return ready


print(pdf_extractor("sampleq.pdf"))