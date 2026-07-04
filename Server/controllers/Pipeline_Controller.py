from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from Services.PipelineService import run_job_pipeline
from Utils.Cv_extractor import extract_cv_text
import os


async def run_pipeline(
    job_title: str = Form(...),
    location: str = Form(...),
    experience: str = Form(...),
    cv_file: UploadFile = File(...)
):
    # handle the file
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{cv_file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await cv_file.read())

    # extract text
    cv_text = extract_cv_text(temp_path)
    os.remove(temp_path)

    # call service and return
    result = run_job_pipeline(job_title, location, experience, cv_text)
    return result


async def download_file(filename: str):
    cv_path = f"outputs/CVs/{filename}"
    root_path = f"outputs/{filename}"

    if os.path.exists(cv_path):
        return FileResponse(cv_path, filename=filename)
    elif os.path.exists(root_path):
        return FileResponse(root_path, filename=filename)

    raise HTTPException(status_code=404, detail="File not found")