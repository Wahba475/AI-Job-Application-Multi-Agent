from fastapi import APIRouter, Depends

from controllers.pipeline_controller import get_pipeline_status, run_pipeline
from middleware.auth_middleware import get_current_user
from middleware.rate_limiter_middleware import PipelineLimit

router = APIRouter(dependencies=[Depends(get_current_user)])

# Expensive start — rate limited. Status polls freely under auth.
# CV + spreadsheet downloads are served by the /history endpoints.
router.post("/run-pipeline", dependencies=[Depends(PipelineLimit)])(run_pipeline)
router.get("/status/{job_id}")(get_pipeline_status)
