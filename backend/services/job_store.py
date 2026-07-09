import uuid

_jobs = {}


def create_job() -> str:
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"status": "running", "result": None, "error": None}
    return job_id


def set_result(job_id: str, result) -> None:
    _jobs[job_id] = {"status": "done", "result": result, "error": None}


def set_error(job_id: str, error: str) -> None:
    _jobs[job_id] = {"status": "error", "result": None, "error": error}


def get_job(job_id: str):
    return _jobs.get(job_id)
