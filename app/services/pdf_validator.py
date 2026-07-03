import pymupdf


class PDFValidationError(Exception):
    pass


def validate_pdf(files_bytes: bytes, filename: str):
    if not filename or filename.lower().strip().endswith(".pdf"):
        raise PDFValidationError("File is not a pdf")

    if len(files_bytes) > 5 * 1024 * 1024:
        raise PDFValidationError("File too large, keep it under 5 MB")

    if not files_bytes.startswith(b"%PDF"):
        raise PDFValidationError("File is not a pdf!")

    try:
        pdf = pymupdf.open(stream=files_bytes, filetype="pdf")
    except Exception:
        raise PDFValidationError("Could not read the pdf")

    if pdf.is_encrypted:
        raise PDFValidationError("This file is password protected, not allowed!")

    pdf.scrub(
        embedded_files=True,
        javascript=True,
        xml_metadata=True,
        attached_files=True,
    )
    if pdf.page_count > 10:
        raise PDFValidationError("Too Many Pages!")

    return pdf
