# Auth System — Design Notes 2nd July

## Overview
Registration and login flow built with FastAPI, SQLAlchemy, bcrypt, and JWT.
Covers input validation, password hashing, duplicate-email protection, and
token issuance/verification.

---

## Validation helpers

### `helper_name`
Rejects names shorter than 5 characters, or containing digits/special
characters. Meant to catch obviously invalid input, not to be a full name
validator (spaces/hyphens still allowed).

### `helper_password`
Enforces password complexity: minimum length, at least one lowercase,
one uppercase, one digit, one special character. Used only at
**registration** time — not during login, since login should just check the
password against the stored hash, not re-validate formatting rules.

### `helper_email`
Checks whether an email already exists in the DB. Returns `False` if it
does (used during registration to block duplicate sign-ups). This is a
UX-layer check only — see "Race condition" below for why it's not sufficient
on its own.

---

## Registration (`register_user`)

Flow:
1. Validate `name` via `helper_name`.
2. Validate `email` uniqueness via `helper_email`.
3. Validate + hash `password` via `hash_pw` (which calls `helper_password`
   internally and returns `None` if validation fails).
4. Insert the new user row.
5. Return `True`/`False` — never `None`, to avoid falsy-value bugs where
   callers do `if not register_user(...)`.

### Race condition on duplicate email
`helper_email`'s check-then-insert isn't atomic. Two concurrent requests
with the same email could both pass the `helper_email` check before either
has inserted. The actual guarantee against duplicates is the `UNIQUE`
constraint on the `email` column at the DB level.

To handle this safely:
```python
try:
    with db() as session:
        session.execute(insert_stmt)
except IntegrityError:
    return False
```

**Why the split matters:**
- `helper_email` = fast, friendly first line of defense (good UX, catches
  99% of cases cheaply, gives clear error message).
- `IntegrityError` catch around the insert = the real safety net that
  catches the rare race-condition case the first check misses.

---

## Password hashing (`hash_pw`)
Uses `bcrypt`. Salt is generated per-password and embedded directly inside
the resulting hash string (`bcrypt` handles this automatically — no need to
store the salt separately).

```python
salt = bcrypt.gensalt()
hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)
```

Returns `None` if `helper_password` validation fails, so callers can check
`if not hashed: return False` before attempting the insert.

**Storage note:** `bcrypt.hashpw` returns `bytes`. Depending on the DB
column type, may need `.decode('utf-8')` before storing, and `.encode()`
again when reading it back for comparison.

---

## Login (`login_user`)
Deliberately does **not** reuse `helper_email` / `helper_password` — those
are registration-only concerns (checking *availability* / *format* of new
input), not what login needs (checking *correctness* of existing
credentials).

```python
def login_user(email, password):
    email = email.lower().strip()
    with db() as session:
        stmt = select(Users).where(Users.email == email)
        user = session.scalar(stmt)

        if not user:
            return None
        if not bcrypt.checkpw(password.encode('utf-8'), user.password):
            return None
        return user
```

Returns the `Users` object on success, `None` on failure — not a plain
bool — so the calling route can pull `user.id` / `user.email` off it to
build the JWT payload.

### How `bcrypt.checkpw` works
The salt isn't stored separately — it's embedded in the stored hash string
itself (`$2b$12$<salt><hash>`). `checkpw`:
1. Extracts the salt from the stored hash.
2. Re-hashes the plaintext password using that same salt.
3. Compares the two hashes in constant time (avoids timing attacks).

No manual salt handling needed on login — only `gensalt()` at registration.

### Security note: don't leak which emails exist
Login should return the same generic "invalid credentials" error whether
the email doesn't exist or the password is wrong. Returning different
errors for each case is an email-enumeration vulnerability.

---

## `db()` context manager
```python
@contextmanager
def db():
    session = session_db()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```
- Auto-commits on clean exit, rolls back on any exception, always closes
  the session.
- Deliberately generic: doesn't know or care what operation is running
  inside it. Re-raises so the *caller* decides what a given exception means
  in their specific context.
- `except Exception` (not bare `except:`) so `SystemExit` /
  `KeyboardInterrupt` aren't accidentally swallowed if the `raise` is ever
  removed in a future refactor.

**Division of responsibility:**
- `db()` → generic rollback/cleanup, reusable everywhere.
- Business logic (`register_user`, etc.) → catches specific, meaningful
  exceptions (`IntegrityError`) where it actually knows what a failure
  means and what to do about it.

---

## JWT issuance & verification (FastAPI routes)

### Known bugs fixed during review
- `register_user(request.email, request.password, request.name)` had
  arguments in the wrong order vs. the function signature
  `register_user(name, email, password)` — fixed to
  `register_user(request.name, request.email, request.password)`.
- `login_user` originally returned a plain bool, but the route tried to
  access `result.user_id` / `result.email` — fixed by having `login_user`
  return the `Users` object (or `None`) instead.

### Token creation
```python
def create_user_access_token(user_id, email, time):
    time = datetime.now(timezone.utc) + time
    payload = {"sub": str(user_id), "email": email, "exp": time}
    return jwt.encode(payload, os.getenv('JWT_KEY'), os.getenv('JWT_ALG'))
```
15-minute expiry. `JWT_KEY` and `JWT_ALG` must be set in the environment —
worth an assertion at startup so a missing env var fails loudly and early
instead of producing a cryptic runtime error.

### Token verification (`get_current_user` dependency)
```python
def get_current_user(token: str = Depends(oauth2)):
    try:
        payload = jwt.decode(token, key=os.getenv('JWT_KEY'),
                              algorithms=[os.getenv('JWT_ALG')])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired Token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid Token")
```
Used as a FastAPI dependency to protect routes (e.g. `/auth/me`).

---

## Error handling philosophy (general takeaway)
- Catch exceptions **close to where you can do something sensible with
  them** (e.g. `IntegrityError` → return `False` in `register_user`).
- Let unexpected exceptions **propagate up** to be logged/surfaced rather
  than silently swallowed — don't wrap everything in blanket
  `try/except: return False`, or real bugs get hidden behind generic
  failures.
- "Propagate up" = an uncaught exception keeps travelling through the call
  stack (function → caller → caller's caller ...) until something catches
  it or it reaches the top and crashes the program.

---

## PDF Parsing Pipeline (added 5th July)

### Overview
CV is parsed from PDF to markdown using `pymupdf4llm.to_markdown()`, then
split into sections by detecting markdown headers, then chunked and prepared
for embedding. The output is a flat list of dicts ready to pass to
sentence-transformers and ChromaDB.

> **Superseded — see "Why the markdown approach was abandoned" below.**
> The `pymupdf4llm.to_markdown()` approach documented in this section works
> for simple single-column PDFs with real (non-image) text, but broke down
> on resumes using decorative image-based section headers. Kept here for
> the regex/bug-fixing history; the current implementation uses the manual
> vector-text + per-image-OCR pipeline described further below.

---

### Regex explained — `HEADER_LINE_RE`
```python
HEADER_LINE_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
```
`pymupdf4llm` converts PDFs to markdown, so section headers become
`# Skills` or `## Experience`. This regex finds those lines:

- `^` — start of a line (works per-line because of `re.MULTILINE`)
- `(#{1,6})` — captures 1–6 `#` characters (markdown heading levels 1–6)
- `\s+` — one or more spaces after the `#`
- `(.*)$` — captures the actual header text up to end of line
- `m.group(1)` = the `##` part, `m.group(2)` = the label e.g. "Experience"

---

### `split_markdown_to_chunks` — how it works
1. Finds all markdown header lines in the document using `HEADER_LINE_RE`
2. Classifies each header against `HEADER_PATTERNS` (skills, education, experience, projects)
3. Everything before the first classified header → `chunks["intro"]`
4. For each classified header, slices the markdown from that header's end to the next header's start
5. Returns a dict: `{"skills": "text...", "education": "text...", "projects": ["p1...", "p2..."]}`

**Bug fixed:** the original `end = len(md)` was outside the `else` block,
meaning every section grabbed text all the way to the end of the document.
Fixed by adding `else: end = len(md)` so only the last section gets that default.

---

### `chunk_for_embedding` — why it exists and the critical type rule
Sections over 1500 chars get split into smaller paragraphs (split on `\n\n`,
merged into ~1500 char blocks). Sections under 1500 chars are kept whole.

**Critical rule: this function must always return `dict[str, list[str]]` —
every value is always a list, even if it contains only one item.**

```python
if len(text) < limit:
    out[label] = [text]   # wrap in list — NOT just `text`
    continue
```

If a short section returns a plain string instead of a list and you later
call `enumerate()` on it, Python iterates characters instead of chunks,
producing thousands of single-letter items. This is a silent bug — no error
is thrown, the output just looks like `{'id': 'skills_0', 'text': '*'}`.

---

### `prepare_to_embed` — output shape
Converts the section dict into a flat list of dicts ready for ChromaDB:
```python
[
  {"id": "skills_0", "text": "Python, Java, SQL...", "section": "skills"},
  {"id": "projects_0", "text": "Built FinTracker...", "section": "projects"},
  {"id": "projects_1", "text": "indianhive.se...", "section": "projects"},
]
```
Each item has a unique `id` (section + index), the raw text, and the section
label as metadata. This list passes directly to the embedder.

**Later addition:** `intro` is explicitly skipped inside `prepare_to_embed`
(not just left unused but actively filtered) — deliberate V1 decision,
contact info isn't meaningful for semantic matching. Known accepted risk:
if a resume's first real section uses a header phrasing not in
`HEADER_PATTERNS`, that unrecognized section's content silently gets
absorbed into `intro` and is now genuinely lost, not just mislabeled.
Cheap mitigation considered but not yet built: log a warning if `intro`
content exceeds ~300 chars, as a signal to manually check that resume.

---

### Section split — JD-dependent vs JD-independent
Not all sections need embedding or gap analysis:

- **Personal info + intro** — skip embedding. Name, email, LinkedIn are
  structured data, not meaningful for semantic search against JD requirements.
- **Education** — originally scoped to skip embedding, extracted as
  structured data instead. In practice ended up embedded and stored
  alongside skills/experience/projects, and it turned out to matter — see
  "Bug: JD requirements over-merged" below, where retrieving the resume's
  real education chunk correctly depended on it being in the collection.
- **Experience + Skills + Projects** — embedded and stored in ChromaDB.
  Gap analysis queries each JD requirement against these sections (plus
  education, per above) to find what's missing or weak in the CV.

---

### Key bug pattern to remember
```python
enumerate(some_dict)    # → (index, key)       WRONG
enumerate(some_string)  # → (index, character)  WRONG
enumerate(some_list)    # → (index, item)        CORRECT

some_dict.items()       # → (key, value)         CORRECT for dicts
```
Always use `.items()` when iterating a dict. Always ensure data is a list
before calling `enumerate`.

---

### Default argument + f-string bug (Python 3.11)
Python 3.11 does not allow same-type nested quotes inside f-strings:
```python
# BROKEN in 3.11
def func(path=f"{os.getenv("FILE_PATH")}/file.md"):
```
Fix: use different quote types, or compute the default inside the function body:
```python
# CORRECT
def func(path=None):
    if path is None:
        path = os.path.join(os.getenv("FILE_PATH"), "file.md")
```
The second approach is also better practice — default argument values are
evaluated once at import time, so if the env var isn't loaded yet, the
f-string approach silently produces `None/file.md`.

**Real recurrence of this exact bug:** hit again in `pdf_extractor.py`'s
`convert_pdf_to_markdown(filename, md_path=f"{os.getenv('FILE_PATH')}...")`.
Traceback showed a literal filename of `"Nonesampleq.pdf"` — `os.getenv`
returned `None`, and the f-string silently stringified it to `"None"`
rather than raising. Root cause was `load_dotenv()` not having run yet
relative to where the default was evaluated. Confirms this bug doesn't
announce itself — it produces a garbled path that reads like a typo until
traced back.

---

### Why the markdown approach was abandoned (added 5th July, later same day)

`pymupdf4llm.to_markdown()` looked like it handled multi-column layout and
header detection automatically — it doesn't reliably do either once real
resume templates get involved. Two separate failures found by testing
against actual two-column resumes with image-based section headers:

**1. Column interleaving.** On a two-column resume, blocks were emitted in
raw top-to-bottom `y`-position order across the *whole page width*, not
grouped by column first. A right-column job entry and a left-column
sidebar header at similar `y` positions ended up adjacent in the markdown
output, as if sequential — headers from one column showing up mid-content
of the other.

**2. Image-header OCR mode swallows nearby vector text.** Some resumes
render section titles (`CONTACT`, `SKILLS`, `WORK EXPERIENCE`) as images
(decorative colored bars), not real PDF text. `pymupdf4llm` OCRs these into
`<!-- Start of picture text --> ... <!-- End of picture text -->` comment
blocks — but on pages containing such an image, it appears to shift into a
different processing mode and silently drops surrounding *vector* text
entirely. Confirmed by isolated test: a page with a plain (non-text) image
kept all its vector text; a page with an OCR-able text image lost it.
This is an opaque library heuristic, not something reliably tunable via
parameters — cropping the page to work around column interleaving made it
worse, since `set_cropbox` physically slices images at the crop boundary,
corrupting the OCR of anything straddling that line.

**Replacement approach — manual vector + per-image OCR, no page cropping:**
1. `page.get_text("dict")` → real vector text blocks, each with its own bbox.
2. `page.get_image_info()` → locate every embedded image's bbox, render
   *just that image's own region* via `page.get_pixmap(clip=rect, dpi=300)`,
   OCR it directly with `pytesseract`. The page itself is never cropped, so
   no image is ever physically cut before OCR sees it.
3. Merge both lists, tagged with `source: "text"` / `"image_ocr"`.
4. Column split: cluster block x-ranges into merged horizontal bands: gap
   between bands > threshold ⇒ two columns. Bin blocks by bbox center-x,
   sort each column top-to-bottom by `y0` independently, concatenate
   left-column-then-right-column.
5. Walk the final ordered block list directly (no markdown, no
   regex-over-one-giant-string): a block becomes a section boundary if its
   own (short, cleaned) text matches a keyword; everything else
   accumulates as body text for whichever section is currently "open."

V1 scope decision: most target resumes (Swedish market) are single-column,
so column-detection is currently unused in practice but kept in the code
as a guard rather than removed, in case a two-column resume is submitted.

---

## JD Parsing Pipeline (added 5th July)

### Overview
Job descriptions arrive as **plain text only** (pasted into a request
body — no PDF, no file upload), which sidesteps everything in the PDF
pipeline above (no OCR, no column detection, no layout ambiguity). The
pipeline is: detect section boundaries on the raw text first → slice into
`{category: full_text}` → THEN size-chunk each section's body → flatten
into embed-ready dicts.

**Core rule carried over from the PDF pipeline and re-confirmed here:
structure-aware splitting always happens before size-aware splitting,
never the reverse.**

---

### Categories
```python
TITLES_PATTERN = {
    "requirements": r"requirements|qualifications|required qualifications|"
                     r"minimum qualifications|what you'll need|what you need|"
                     r"must haves|skills & requirements|basic qualifications|"
                     r"what we're looking for|who you are|experience required",
    "optional": r"additional qualifications|bonus points|bonus skills|"
                r"desired skills|extra credit|good to have|nice to have|"
                r"pluses|preferred qualifications|preferred skills|"
                r"what would be great",
    "responsibilities": r"core responsibilities|day-to-day|duties|job duties|"
                         r"key responsibilities|responsibilities|"
                         r"the impact you'll have|the role|"
                         r"what you'll be doing|what you'll do|your role|"
                         r"accountabilities",
}

# Final version, after generalizing "about us" -> "about ANY company name":
IGNORE_PATTERN = (r"benefits|perks|how (?:it|jobgether) works|why apply|"
                   r"data privacy notice|about\s+\w+|equal opportunity|"
                   r"practical details|why this role|the team")
```
`IGNORE_PATTERN` covers boilerplate — matched as a boundary like any real
category, but its content is discarded rather than stored
(`sections.pop("__ignore__")` before returning).

`intro` is kept in the section dict but dropped before the embedding stage.

---

### `classify_line` — two header shapes, both anchored at line-start

```python
def classify_line(line):
    cleaned = line.strip()
    if not cleaned:
        return None, None

    bare = cleaned.lower().rstrip(":?")
    if len(bare.split()) <= 6:
        for category, pattern in TITLES_PATTERN.items():
            if re.match(rf"^(?:{pattern})\b", bare):
                return category, ""
        if re.match(rf"^(?:{IGNORE_PATTERN})\b", bare):
            return "__ignore__", ""

    for category, pattern in TITLES_PATTERN.items():
        m = re.match(rf"^(?:{pattern})\s*[:\-]\s*(.+)$", cleaned, re.IGNORECASE)
        if m:
            return category, m.group(1).strip()

    m = re.match(rf"^(?:{IGNORE_PATTERN})\s*[:\-]\s*(.+)$", cleaned, re.IGNORECASE)
    if m:
        return "__ignore__", m.group(1).strip()

    return None, None
```

**Shape 1 — bare/short header.** `re.match` + `\b` (prefix match), not
`re.fullmatch` — a title can have a couple extra trailing words and still
count, as long as it's short (≤6 words) and *starts with* the keyword.

**Shape 2 — inline-prefaced header**, e.g. `"Nice to have: experience with
Docker..."` — keyword at line-start, `:`/`-`, with real trailing content
preserved rather than discarded.

**Why anchored at line-start:** stops a sentence merely *mentioning* a
keyword mid-way (e.g. `"Requirements for this role include..."`) from
being mistaken for a boundary.

**Known, accepted V1 gap:** an inline qualifier embedded inside a normal
sentence (no line-start marker) isn't detected. Deferred.

---

### Bug: unintended capturing groups shift `.group()` indices
```python
# BROKEN
IGNORE_PATTERN = r"...|how (it|jobgether) works|...|about (us|the company)|..."
```
Spliced into a bigger pattern, the intended trailing-content group shifts
from `group(1)` to `group(3)` because the two groups inside `IGNORE_PATTERN`
get counted first — `m.group(1)` returns `None` for the alternatives
without their own inner group active, and `.strip()` on `None` crashes.

**Fix:** any parentheses inside a pattern string that will later be
spliced into a bigger regex and indexed via `.group(N)` must be
non-capturing: `(?:...)`.

---

### Bug: `fullmatch` too strict for real-world header phrasing
`"why apply"` (pattern) ≠ `"why apply through jobgether?"` (actual line) —
`fullmatch` demands total equality. **Fix:** `re.match(rf"^(?:{pattern})\b",
bare)` accepts the keyword as a prefix instead.

---

### Bug: last-section end index was a tuple, not an int
```python
# BROKEN
else:
    end = headers[len(headers) - 1]   # a tuple, and even indexed [0],
                                        # points at the CURRENT header, not EOF
```
**Fix:** `end = len(lines)` — "no more headers after this one" means go to
end of document, computed independently, not derived from the boundary list.

---

### Bug: real-world JD used header phrasing outside the pattern set entirely
A live JD used `"Why this role"`, `"Practical details"`, and `"About
Redpine"` — none matched `TITLES_PATTERN` or the original `IGNORE_PATTERN`
(`about (?:us|the company)` only matches the literal words, not an actual
company name). Result: everything from `"What we're looking for"` to the
literal end of the document — including a work-permit requirement AND an
unrelated "founded by ex-Spotify/McKinsey operators" marketing paragraph —
got silently absorbed into `requirements` as one blob. Confirmed via the
LLM feedback step downstream, which faithfully cited the marketing
paragraph as if it were a real requirement — not a hallucination, a real
upstream chunking defect surfacing through an otherwise-correct LLM step.

**Fix:** generalized `about (?:us|the company)` to `about\s+\w+`, and
added `practical details|why this role|the team` to `IGNORE_PATTERN`.

**Open design question, not resolved:** that JD's `"Practical details"`
section mixed genuine candidate-relevant content (Stockholm-based, valid
work permit) with pure boilerplate. Currently discarded wholesale.
Considered but not built: a dedicated `logistics` category instead of
blanket-ignoring. Deferred as acceptable for V1 given target market is
already primarily Sweden-based.

---

### `split_jd_by_headings` — full flow
1. `jd_text.splitlines()`, classify every line, collect
   `(line_index, category, trailing_content)` → `boundaries`.
2. Everything before `boundaries[0]` → `sections["intro"]`.
3. Per boundary: `lines[start:end]`, `start` = line after the header,
   `end` = next boundary's line index (or `len(lines)` for the last one).
4. `trailing_content` (inline-header case) prepended to that section's body.
5. `sections.pop("__ignore__", None)` / `sections.pop("intro", None)`.

**Bug: unsafe dict lookup before pop.** An early version checked
`if sections["__ignore__"]:` before popping — direct bracket lookup raises
`KeyError` outright if the key was never added (e.g. a JD with zero
boilerplate never triggers `__ignore__` at all). Fix: `.pop(key, None)`
already handles "key may not exist" safely in one call — the preceding
`if` was not just redundant but the actual bug. No conditional needed.

---

### Bug: JD requirements over-merged, diluting retrieval (major)

`chunk_to_embed` originally ran `RecursiveCharacterTextSplitter` per
category on the JD side, same as the resume side. For short `requirements`
sections (common — often under 450 chars total), the splitter never split
at all: five distinct bullets (Python, FastAPI, SQL, pytest, "currently
studying...") stayed merged as *one* chunk, embedded and queried as a
single blob.

**Consequence, discovered via gap analysis output:** the merged chunk's
embedding was dominated by keyword-dense technical bullets, so when
queried against the resume it matched `skills` (0.47 distance) and never
even competed against `education` — even though the resume's actual
education chunk existed in the collection and directly addressed the
"currently studying" bullet. The LLM feedback step then correctly,
faithfully reported "no education details found" — a genuine consequence
of one query standing in for what should have been five, not a
hallucination.

**Fix:** JD bullets are already one-per-line in the source text, so
character-count chunking is the wrong tool for this side. Replaced with
line-based splitting:
```python
def chunk_to_embed(chunks: dict):
    final = {}
    for category, text in chunks.items():
        bullets = [line.strip() for line in text.split("\n") if line.strip()]
        final[category] = bullets
    return final
```
Each bullet becomes its own chunk → its own query → a fair chance to match
the specific resume section it's actually about.

**Note:** the resume side still uses `RecursiveCharacterTextSplitter` —
resume prose (especially Experience) doesn't have JD's clean
one-bullet-per-line structure, so this fix doesn't directly transfer.
Flagged as worth re-examining later, not changed yet.

---

## Embedding + ChromaDB Pipeline (added 5th July, later same day)

### Shared client/model module — avoiding accidental side effects on import
Early version had `gap_analyzer.py` doing `from sentence_embedder import
client`. Since Python executes a module top-to-bottom on import, this
silently **re-ran the entire embedding pipeline** (PDF parsing, chunking,
`chunk_embedder` calls) as a side effect of just wanting a client handle.

**Fix:** `client` and `model` pulled into their own module with zero side
effects, imported by every file that needs them:
```python
# chroma_client.py
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path=".../app/chroma_db")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

### `PersistentClient` vs in-memory
In-memory Chroma loses everything on process exit — wrong for a service
where embed-once/query-many across separate requests/restarts is the
point. `PersistentClient(path=...)` writes to disk. Open question, not
yet resolved: whether the deployment target's filesystem (Render) is
ephemeral across redeploys even with `PersistentClient` — needs checking
before shipping, not before local dev.

### Two collections, not one shared collection
`resume` and `job_description` as **separate** Chroma collections rather
than one shared collection with a `type` metadata field — chosen because
the query direction is fixed and one-way (JD chunks as queries *into* the
resume collection, never the reverse), so there's never a need to filter
a shared pool.

Confirmed via `.peek()`: each collection gets its own subdirectory on disk
(named by internal UUID, not the given name) — 2 collections ⇒ exactly 2
folders, consistently, not growing per run. Normal behavior, not a leak.

### Fresh-collection-per-run pattern
Scope: always exactly one resume + one JD per run, no `resume_id`/`jd_id`
scoping needed — but that means **not** clearing collections between runs
would leave stale data from the previous run mixed into the next.
```python
def get_fresh_collection(c, name):
    try:
        c.delete_collection(name)
    except Exception:
        pass
    return c.create_collection(name, metadata={"hnsw:space": "cosine"})
```
(Originally named `create_collection`, misleading since it's destructive —
renamed. Also swapped a bare `except:` for `except Exception:`, same
pattern already flagged for `db()` earlier in these notes.)

**Corollary bug:** plain `client.create_collection(name)` (no delete
first) throws `Collection already exists` on any run after the first,
since `PersistentClient` means prior runs' collections are still on disk.
`get_or_create_collection` alone avoids the crash but silently
accumulates old + new data together — wrong given the "always fresh"
scope decision.

### `chunk_embedder` — shared for both resume and JD sides
```python
def chunk_embedder(chunks: list[dict], collection):
    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    metadata = [{"category": chunk["category"]} for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()
    collection.add(
        ids=ids, documents=texts, embeddings=embeddings, metadatas=metadata
    )
```
Takes `collection` as a parameter so the same function embeds both sides —
called twice, once per collection.

**Bugs caught in earlier drafts:**
- `metadatas` needs a list of **dicts**, not bare strings — Chroma's
  `where` filter needs the dict shape to be queryable.
- `collection.add(...)` accidentally sitting outside the `for` loop (same
  indentation as `for`, not nested) meant only the *last* category
  processed ever got added — every earlier category silently discarded.
- IDs need to be unique **per chunk**. Settled on deterministic string ids
  (`f"{category}_{i}"`) over random `uuid4()` — deterministic means
  re-running the same input during dev overwrites cleanly instead of
  accumulating duplicates, and it's self-descriptive for debugging.

### Bug: `model.encode(text)` vs `model.encode([text])` — batch shape
`encode([text])` returns shape `(1, 384)`; `encode(text)` (bare string)
returns `(384,)`. Chroma's `query_embeddings=` expects a list-of-embeddings
(supports batched queries), so the batch-shaped version is required —
always wrap a single query in `[text]`.

### Bug: Chroma's own default embedding function firing unexpectedly
`resume.query(query_texts=[text], ...)` triggered an unexpected ~80MB ONNX
model download — same `all-MiniLM-L6-v2` architecture, but Chroma's own
bundled copy, since `query_texts=` tells Chroma "embed this yourself,"
and no custom embedding function was attached to the collection. A
different runtime from the `sentence-transformers` instance already used
for storage — an avoidable inconsistency and wasteful re-download.

**Fix:** embed the query explicitly with the same `model`, pass
`query_embeddings=` instead:
```python
query_embedding = model.encode([text], normalize_embeddings=True).tolist()
match = resume.query(query_embeddings=query_embedding, n_results=3)
```
**Related mistake caught along the way:** briefly wrote
`query_texts=query_embedding` — passing a vector into the parameter meant
for raw text. Chroma's own error was directly diagnostic: `Expected
document to be a str, got [-0.0115...]`.

### Normalization + cosine distance — why, and why both sides must match
Unnormalized embeddings + default L2 space gave distances with no fixed,
interpretable range. Switched to `normalize_embeddings=True` on **both**
insert and query sides (must be identical on both, or the two vector sets
live on different scales), and `metadata={"hnsw:space": "cosine"}` at
collection creation time (can't be changed after creation — free to add
since collections are already recreated every run).

Result: distances bounded and interpretable — 0 = identical direction,
1 ≈ unrelated, 2 = opposite. (Cosine *distance*, not *similarity* —
similarity ranges -1 to 1 with 0 = unrelated; `distance = 1 - similarity`,
worth remembering which one's being read since "higher is better" flips.)

**Threshold calibration is empirical, not derivable from first
principles.** Sentence-transformer models encode overall semantic content,
not keyword overlap — genuinely relevant matches rarely land near 0
(that's closer to duplicate/paraphrased text). Real observed anchors:
best real matches ~0.47–0.59; a genuine total gap (zero supporting
content) ~0.90–0.99. Working thresholds, expected to be revisited with
more test data:
- `< 0.70` → covered
- `0.70–0.85` → partial
- `> 0.85` → gap

---

## Gap Analyzer (added 5th July, later same day)

### `get_results` — JD chunks as queries into the resume collection
Chroma has no "compare two collections" operation — always search
*within one* collection using a single query input. Structurally: pull
every JD chunk from `job_description` via `.get()` (plain fetch, no
similarity search), loop over them, issue one `.query()` per chunk *into*
`resume`. Direction is fixed: JD text in, resume matches out, never the
reverse.

`responsibilities` chunks filtered out entirely — they describe the job,
not a checkable candidate qualification. Only `requirements` and
`optional` go through gap analysis. `n_results=3` per query — enough to
see if the best match is genuinely strong vs. the least-bad of a weak
field, without drowning in marginal results.

**Bug: function computed `results` but never returned it** — silently
always gave `None` to the caller.

### `check_gap` — bucketing + evidence attachment
Take the **best** (lowest) of the 3 returned distances per JD chunk —
`matches["distances"][0][0]` — bucket against thresholds, attach the
actual matched resume text and section alongside the verdict (needed so
the LLM step has something concrete to cite, not just a bare number).

**Bug: double-indexing into an already-extracted value.**
```python
resume_section = chunk["matches"]["metadatas"][0][0]["category"]  # already a string
resume_category = resume_section["category"]   # BROKEN — re-indexing a string
```
`TypeError: string indices must be integers, not 'str'` — the first line
already pulls out the plain string; the second tries to index into it
again. Fix: use `resume_section` directly.

**Design note — evidence for `gap` entries is not supporting evidence.**
A `gap` entry's `resume_text` is the *closest available* content, which by
definition doesn't address the requirement. Made explicit in the LLM
prompt: gap "evidence" means "closest available, still doesn't cover it,"
not "proof of coverage" — otherwise the model risks misreading it as support.

---

## LLM Feedback Generation (added 5th July, later same day)

### Grounding against hallucination — concrete techniques
Initial draft handed the model a raw Python dict dump and asked for a
five-section report. Fixes applied:

1. **Pre-format structured data into labeled text** before it reaches the
   prompt, rather than dumping a raw dict — parsing dict/list syntax
   competes with reasoning about content.
2. **Explicit grounding instruction**: base every claim only on the text
   provided; do not infer/assume/invent anything not explicitly present.
3. **Explicit permission to say "not enough information"** rather than
   fabricating content to fill every section — models tend to invent when
   obligated to fill a section, especially "Interview Risk Areas."
4. **Distinguish "closest match" from "supporting evidence"** for GAP
   items directly in the prompt.
5. **Constrain "Resume Improvements" to rephrasing/surfacing existing
   experience**, explicitly forbidding suggesting the candidate add
   experience they don't have.
6. **Low `temperature` (0.2–0.3)** on the API call — reduces speculative
   drift for a task that should be grounded synthesis, not creative writing.

### Real hallucination-adjacent failure caught, and its actual root cause
One run inferred work eligibility from "studies at a Swedish university" —
the resume never states this, and it's not a safe inference (enrollment ≠
work authorization). A genuine, if subtle, grounding failure.

A second run cited the target company's own founders/investors as if it
were a job requirement being measured against the candidate. Traced
upstream — this was **not** hallucination; the company-marketing paragraph
had genuinely been mis-chunked into `requirements` before the LLM ever saw
it (see "real-world JD used header phrasing outside the pattern set"
above). General lesson: when LLM output looks wrong, check whether the
*input it was given* was already wrong before assuming a prompting
problem — the actual fix here was entirely upstream in the JD chunker.

### `Interview Risk Areas` — correct behavior on an empty gap set, not a bug
A strong-match resume-JD pair produced `"gap": []` for both categories,
and the LLM correctly wrote "Not enough information to assess" rather than
manufacturing a risk narrative — constraint #3 above working as intended,
not a defect. But this conflates two different situations under identical
fallback text:
- Genuinely insufficient data to judge (fallback text is accurate)
- Complete data that simply contains **zero** gaps (a positive result,
  currently phrased identically to "I don't know")

Refined the prompt to special-case zero-gap data explicitly, so a strong
match reads as a confident positive result rather than looking like the
model shrugged.

### Validated across three deliberately different test cases
Ran the full pipeline (parse → chunk → embed → retrieve → bucket →
explain) against three JDs against the same resume, chosen to span the
range: a strong match (synthetic junior backend JD written to overlap
with the resume's actual stack), a moderate mismatch (Golang/Linux role),
and a heavy mismatch (senior retrieval/RAG infrastructure role). Output
correctly discriminated between all three — genuine strengths cited with
real resume evidence, genuine gaps flagged plainly, no invented skills or
inflated claims after the grounding fixes above. First end-to-end
validation that the system produces meaningfully different, accurate
output rather than just "running without crashing."

---

## Session reflection (5th July)

First full day building the RAG core: PDF parsing (twice — the
`pymupdf4llm` approach and its manual replacement), JD parsing, chunking
strategy for both, embedding, ChromaDB storage/retrieval, gap bucketing,
and LLM feedback grounding. Every bug in this file above was found by
reading actual debug output and tracing it back — the `__ignore__`
KeyError, the tuple-instead-of-int end index, the capturing-group
`.group()` shift, the query_texts/query_embeddings mixup, the JD
over-merging issue — none of these were guessed at in advance; all were
caught by running real data through the pipeline and noticing when the
output didn't match what it should've been. The Redpine "Company Context"
case in particular was a good instance of correctly diagnosing that an
LLM-looking problem was actually an upstream data problem, rather than
reflexively rewriting the prompt.

Two things intentionally left as open V1 gaps rather than fixed today,
worth revisiting later: (1) resume-side chunking still uses
character-count splitting, not the bullet-level fix applied to the JD
side — flagged as inconsistent but not yet proven to matter in practice;
(2) `"Practical details"`-style JD sections that mix genuine
location/eligibility requirements with pure boilerplate are currently
discarded wholesale rather than partially kept.