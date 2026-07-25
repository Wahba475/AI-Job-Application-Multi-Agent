"""Pipeline CONTROLLER — /run-pipeline (auth-gated) + status polling.

Flow of a run:
  1. Validate the upload (extension + magic bytes + size).
  2. Extract CV text (never 500s — bad files return 400).
  3. Start a background job (job_id == run_id).
  4. Background: stream the pipeline (reporting each step) → upload deliverables
     to Supabase → insert one history row (with per-job results) → store the
     frontend payload in the job store.
"""
import asyncio
import logging
import os

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile

from middleware.auth_middleware import get_current_user
from services.job_store import create_job, get_job, set_error, set_result, set_step
from services.pipeline_service import run_job_pipeline
from services import deliverable_service, history_service
from utils.cv_extractor import extract_cv_text

logger = logging.getLogger("applyai.pipeline")

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}
MAX_CV_SIZE = 5 * 1024 * 1024  # 5 MB
# Magic bytes: PDF = "%PDF", DOCX = ZIP container "PK\x03\x04".
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"

_background_tasks: set = set()


def _validate_upload_headers(ext: str, content_length: str | None) -> None:
    if ext not in ALLOWED_CV_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .pdf and .docx CVs are accepted")
    # Coarse pre-check on the whole multipart body before we read it.
    if content_length and content_length.isdigit() and int(content_length) > MAX_CV_SIZE + 1024 * 1024:
        raise HTTPException(status_code=413, detail="CV file too large (max 5 MB)")


def _validate_content(ext: str, contents: bytes) -> None:
    if len(contents) > MAX_CV_SIZE:
        raise HTTPException(status_code=400, detail="CV file too large (max 5 MB)")
    if ext == ".pdf" and not contents.startswith(_PDF_MAGIC):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")
    if ext == ".docx" and not contents.startswith(_ZIP_MAGIC):
        raise HTTPException(status_code=400, detail="File is not a valid DOCX")


async def run_pipeline(
    request:    Request,
    job_title:  str        = Form(...),
    location:   str        = Form(...),
    experience: str        = Form(...),
    cv_file:    UploadFile = File(...),
    user:       dict       = Depends(get_current_user),
):
    ext = os.path.splitext(cv_file.filename or "")[1].lower()
    _validate_upload_headers(ext, request.headers.get("content-length"))

    contents = await cv_file.read()
    _validate_content(ext, contents)

    # Extract text — a malformed file must be a clean 400, never a 500.
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", f"{os.urandom(8).hex()}{ext}")
    with open(temp_path, "wb") as f:
        f.write(contents)
    try:
        cv_text = extract_cv_text(temp_path)
    except Exception as e:
        logger.warning("CV extraction failed: %s", e)
        raise HTTPException(status_code=400, detail="Could not read the CV file. Please upload a valid PDF or DOCX.")
    finally:
        os.remove(temp_path)

    if not cv_text or not cv_text.strip():
        raise HTTPException(status_code=400, detail="The uploaded CV appears to be empty or unreadable.")

    job_id = create_job()          # job_id doubles as run_id
    user_id = user["id"]

    async def _run_job():
        try:
            result = await asyncio.to_thread(
                run_job_pipeline, job_id, job_title, location, experience, cv_text,
                lambda node: set_step(job_id, node),
            )
        except Exception as e:
            logger.exception("Pipeline failed job=%s", job_id)
            set_error(job_id, "Pipeline run failed. Please try again.")
            return

        job_results = result.get("job_results", [])
        if not job_results:
            set_result(job_id, {**result, "history_id": None, "jobs": []})
            return

        # Persist deliverables (CVs + spreadsheet) to Supabase.
        try:
            set_step(job_id, "uploading")
            persisted = await asyncio.to_thread(
                deliverable_service.finalize_run, user_id, job_id, job_results)
        except Exception as e:
            logger.exception("Deliverable upload failed job=%s", job_id)
            set_error(job_id, "Run completed but files could not be saved. Please try again.")
            return

        # Insert the history row (per-job results incl. CV storage paths).
        try:
            entry = history_service.create_history_entry(
                user_id=user_id, run_id=job_id,
                job_title=job_title, location=location, experience=experience,
                spreadsheet_bucket=persisted["spreadsheet_bucket"],
                spreadsheet_path=persisted["spreadsheet_path"],
                jobs=persisted["jobs"],
            )
            history_id = entry["id"]
        except Exception as e:
            logger.exception("History insert failed job=%s", job_id)
            set_error(job_id, "Run completed but history could not be saved.")
            return

        # Frontend payload — CV/spreadsheet served via the auth history endpoints.
        frontend_jobs = []
        for idx, (jr, pj) in enumerate(zip(job_results, persisted["jobs"])):
            frontend_jobs.append({
                "index":       idx,
                "title":       pj["title"],
                "company":     pj["company"],
                "location":    pj["location"],
                "type":        pj["type"],
                "apply_link":  pj["apply_link"],
                "ats_score":   pj["ats_score"],
                "gaps":        pj["gaps"],
                "tailored":    pj["tailored"],
                "cv_filename": pj["cv_filename"],
                "cv_text":     jr.get("cv_text", ""),
            })

        set_result(job_id, {
            "run_id":         job_id,
            "history_id":     history_id,
            "total_jobs":     result["total_jobs"],
            "approved_count": result["approved_count"],
            "retry_rounds":   result["retry_rounds"],
            "jobs":           frontend_jobs,
        })

    task = asyncio.create_task(_run_job())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"job_id": job_id}


async def get_pipeline_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
