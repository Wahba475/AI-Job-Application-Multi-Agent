from fastapi import APIRouter
from controllers.pipeline_controller import run_pipeline, download_file

router = APIRouter()

router.post("/run-pipeline")(run_pipeline)
router.get("/download/{filename}")(download_file)