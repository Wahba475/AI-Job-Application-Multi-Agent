from fastapi import APIRouter
from controllers.pipeline_controller import run_pipeline, get_pipeline_status, download_file

router = APIRouter()

router.post("/run-pipeline")(run_pipeline)
router.get("/status/{job_id}")(get_pipeline_status)
router.get("/download/{filename}")(download_file)
