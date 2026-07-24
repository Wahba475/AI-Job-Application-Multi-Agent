from fastapi import APIRouter, Depends

from controllers.pipeline_controller import download_file, get_pipeline_status, run_pipeline
from middleware.auth_middleware import get_current_user
from middleware.rate_limiter_middleware import PipelineLimit

router = APIRouter(dependencies=[Depends(get_current_user)])

# Expensive start — rate limited. Status/download poll freely under auth.
router.post("/run-pipeline", dependencies=[Depends(PipelineLimit)])(run_pipeline)
router.get("/status/{job_id}")(get_pipeline_status)
router.get("/download/{filename}")(download_file)
