import os
import tempfile
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.pdf_validator import validate_pdf, PDFValidationError
from app.services.pdf_extractor import convert_pdf_to_markdown, split_markdown_to_chunks, chunk_for_embedding, \
    prepare_to_embed
from app.services.jd_validator import validate_jd
from app.services.jd_extracter import split_header, chunk_to_embed, proper_meta_data
from app.services.gap_analyzer import get_results, check_gap
from app.services.feedback import get_results_feedback,build_prompt, llm_feedback
from pydantic import BaseModel
from starlette import status
from app.chroma_client import client
from typing import Annotated
from app.dependencies import get_current_user
from app.services.sentence_embedder import create_resume_collection, create_jd_collection

router = APIRouter(
    prefix="/analyze",
    tags=["analyze"]
)


class UserUploadRequest(BaseModel):
    filename: str
    job_id: str


class UserUploadJobDesc(BaseModel):
    description: str
    job_id: str


@router.post("/upload_resume", response_model=UserUploadRequest)
async def user_upload_pdf(user_id: Annotated[uuid.UUID, Depends(get_current_user)], file: Annotated[UploadFile, File()]):
    filebytes = await file.read()
    try:
        validate_pdf(filebytes)
    except PDFValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job_id = uuid.uuid4().hex
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
        temp.write(filebytes)
        temp_path = temp.name
    try:
        pdf_to_md = convert_pdf_to_markdown(temp_path, job_id)
        chunks = split_markdown_to_chunks(pdf_to_md)
        chunked = chunk_for_embedding(chunks)
        ready = prepare_to_embed(chunked)
    finally:
        os.unlink(temp_path)
    create_resume_collection(job_id, ready)
    return {"filename": file.filename, "status": "sucess", "job_id": job_id}


@router.post(path="/upload/job_description")
async def user_input_jd(user_id: Annotated[uuid.UUID, Depends(get_current_user)], request: UserUploadJobDesc):
    jd_text = request.description
    job_id = request.job_id
    try:
        cleaned = validate_jd(jd_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    header = split_header(cleaned)
    chunks = chunk_to_embed(header)
    metadata = proper_meta_data(chunks)

    create_jd_collection(job_id, metadata)
    return {"Message": "Success"}


@router.post(path="/analyze/{job_id}")
async def analyze(user_id: Annotated[uuid, Depends(get_current_user)], job_id: str):
    if job_id == "None":
        raise HTTPException(status_code=404, detail="Job not found")

    cv_collection = client.get_collection(f"resume_{job_id}")
    jd_collection = client.get_collection(f"jd_{job_id}")

    collection_chunk = get_results(cv_collection, jd_collection)
    gap_analysis = check_gap(collection_chunk)

    #LLM input
    llm_chunks = get_results_feedback(gap_analysis)
    prompt = build_prompt(llm_chunks)
    llm_response = llm_feedback(prompt)

    return llm_response






