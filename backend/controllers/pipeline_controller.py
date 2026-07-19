"""Pipeline CONTROLLER — handles /run-pipeline and job-status polling.

What changed in this version:
  - run_pipeline() now requires authentication (Depends(get_current_user)).
    The authenticated user_id is needed to scope the history record.
  - The background task _run_job() now:
      1. Runs the LangGraph pipeline (unchanged).
      2. Uploads outputs/jobs.xlsx to Supabase Storage.
      3. Inserts one history record.
      4. Handles partial failures with a compensating delete
         (see the upload/history block for the full failure strategy).
"""
import asyncio
import os
import uuid

from fastapi import Depends, File, Form, HTTPException, UploadFile

from middleware.auth_middleware import get_current_user
from services.job_store import create_job, get_job, set_error, set_result
from services.pipeline_service import run_job_pipeline
from services import storage_service
from services import history_service
from utils.cv_extractor import extract_cv_text

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}
MAX_CV_SIZE            = 5 * 1024 * 1024  # 5 MB

# Keep references so background tasks are not garbage-collected mid-run.
_background_tasks: set = set()


async def run_pipeline(
    job_title:  str        = Form(...),
    location:   str        = Form(...),
    experience: str        = Form(...),
    cv_file:    UploadFile = File(...),
    user:       dict       = Depends(get_current_user),   # ← auth added
):
    # ── CV validation ─────────────────────────────────────────────────────────
    ext = os.path.splitext(cv_file.filename or "")[1].lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .pdf and .docx CVs are accepted")

    contents = await cv_file.read()
    if len(contents) > MAX_CV_SIZE:
        raise HTTPException(status_code=400, detail="CV file too large (max 5 MB)")

    # ── Write to temp, extract text, clean up ─────────────────────────────────
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", f"{uuid.uuid4().hex}{ext}")
    with open(temp_path, "wb") as f:
        f.write(contents)
    try:
        cv_text = extract_cv_text(temp_path)
    finally:
        os.remove(temp_path)

    # ── Kick off background job ───────────────────────────────────────────────
    job_id = create_job()

    async def _run_job():
        # ── 1. Run the LangGraph pipeline ────────────────────────────────────
        try:
            result = await asyncio.to_thread(
                run_job_pipeline, job_title, location, experience, cv_text
            )
        except Exception as e:
            print(f"[PIPELINE] job={job_id} failed: {e}")
            set_error(job_id, "Pipeline run failed. Please try again.")
            return

        # ── 2. Upload jobs.xlsx to Supabase Storage ───────────────────────────
        xlsx_path = os.path.join("outputs", "jobs.xlsx")
        if not os.path.exists(xlsx_path):
            print(f"[PIPELINE] job={job_id}: jobs.xlsx not found — skipping upload")
            set_result(job_id, result)
            return

        try:
            with open(xlsx_path, "rb") as f:
                xlsx_bytes = f.read()

            bucket, path = storage_service.upload_file(
                user_id      = user["id"],
                run_id       = job_id,
                filename     = "jobs.xlsx",
                data         = xlsx_bytes,
                content_type = storage_service.XLSX_MIME,
            )
        except Exception as upload_err:
            # Upload failed — nothing was written to storage or DB.
            # Pipeline result is still useful so we preserve it.
            print(f"[PIPELINE] job={job_id}: storage upload failed: {upload_err}")
            set_result(job_id, {**result, "history_id": None, "storage_error": str(upload_err)})
            return

        # ── 3. Save history record ────────────────────────────────────────────
        # Failure strategy: if the DB insert fails after a successful upload,
        # we immediately delete the uploaded file (compensating action) so no
        # orphaned objects are left in storage.
        try:
            entry = history_service.create_history_entry(
                user_id            = user["id"],
                job_title          = job_title,
                location           = location,
                experience         = experience,
                spreadsheet_bucket = bucket,
                spreadsheet_path   = path,
            )
            history_id = entry["id"]
        except Exception as db_err:
            print(f"[PIPELINE] job={job_id}: history insert failed: {db_err} — compensating")
            try:
                storage_service.delete_file(bucket, path)
                print(f"[PIPELINE] job={job_id}: orphaned file cleaned up successfully")
            except Exception as cleanup_err:
                # Both the DB write and the compensating delete failed.
                # Log the exact path so it can be removed manually.
                print(
                    f"[CRITICAL] Orphaned file — manual cleanup required: "
                    f"bucket={bucket}, path={path} | "
                    f"db_err={db_err} | cleanup_err={cleanup_err}"
                )
            set_error(job_id, "Pipeline completed but history could not be saved.")
            return

        # ── 4. Everything succeeded ───────────────────────────────────────────
        set_result(job_id, {**result, "history_id": history_id})

    task = asyncio.create_task(_run_job())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"job_id": job_id}


async def get_pipeline_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def download_file(filename: str):
    """Serve a file directly from the local outputs/ directory.

    This endpoint is kept for backward compatibility (e.g. CV .docx files).
    Spreadsheets are now served via /history/{id}/download instead.
    """
    safe_name    = os.path.basename(filename)
    outputs_root = os.path.realpath("outputs")

    for candidate in (
        os.path.join(outputs_root, "CVs", safe_name),
        os.path.join(outputs_root, safe_name),
    ):
        resolved = os.path.realpath(candidate)
        if resolved.startswith(outputs_root + os.sep) and os.path.exists(resolved):
            from fastapi.responses import FileResponse
            return FileResponse(resolved, filename=safe_name)

    raise HTTPException(status_code=404, detail="File not found")
