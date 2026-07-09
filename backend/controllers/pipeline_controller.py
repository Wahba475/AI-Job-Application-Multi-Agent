import asyncio
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from services.pipeline_service import run_job_pipeline
from services.job_store import create_job, set_result, set_error, get_job
from utils.cv_extractor import extract_cv_text
import os
import uuid

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}
MAX_CV_SIZE = 5 * 1024 * 1024  # 5 MB

# Keep references so background jobs aren't garbage-collected mid-run
_background_tasks = set()


async def run_pipeline(
    job_title:  str = Form(...),
    location:   str = Form(...),
    experience: str = Form(...),
    cv_file: UploadFile = File(...)
):
    ext = os.path.splitext(cv_file.filename or "")[1].lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .pdf and .docx CVs are accepted")

    contents = await cv_file.read()
    if len(contents) > MAX_CV_SIZE:
        raise HTTPException(status_code=400, detail="CV file too large (max 5MB)")

    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", f"{uuid.uuid4().hex}{ext}")
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        cv_text = extract_cv_text(temp_path)
    finally:
        os.remove(temp_path)

    job_id = create_job()

    async def _run_job():
        try:
            result = await asyncio.to_thread(run_job_pipeline, job_title, location, experience, cv_text)
            set_result(job_id, result)
        except Exception as e:
            print(f"[PIPELINE] Job {job_id} failed: {e}")
            set_error(job_id, "Pipeline run failed. Please try again.")

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
    safe_name = os.path.basename(filename)
    outputs_root = os.path.realpath("outputs")

    for candidate in (os.path.join(outputs_root, "CVs", safe_name), os.path.join(outputs_root, safe_name)):
        resolved = os.path.realpath(candidate)
        if resolved.startswith(outputs_root + os.sep) and os.path.exists(resolved):
            return FileResponse(resolved, filename=safe_name)

    raise HTTPException(status_code=404, detail="File not found")
