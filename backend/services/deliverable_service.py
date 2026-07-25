"""Deliverable SERVICE — turns the pipeline's local files into persisted,
downloadable deliverables.

Flow (called by the pipeline controller after a run finishes):
  1. Upload each generated CV .docx to Supabase Storage.
  2. Build the spreadsheet with pre-signed CV links (so they work from Excel).
  3. Upload the spreadsheet.
  4. Return the jobs[] JSONB (with per-CV storage paths) + spreadsheet path for
     the history row.
  5. Clean up the local run directory — nothing is left on disk.
"""
import os
import shutil

from ai.tools.spreadsheet_builder import build_xlsx
from services import storage_service


def finalize_run(user_id: str, run_id: str, job_results: list[dict]) -> dict:
    """Persist all deliverables for one run. Returns:
        { "jobs": [...], "spreadsheet_bucket": str, "spreadsheet_path": str }
    Each jobs[] element carries the CV's storage bucket/path so it can be
    served later via the auth-protected endpoint.
    """
    jobs = []

    for job in job_results:
        entry = {
            "title":       job.get("title", ""),
            "company":     job.get("company", ""),
            "location":    job.get("location", ""),
            "type":        job.get("employment_type", ""),
            "posted_at":   job.get("posted_at", ""),
            "apply_link":  job.get("apply_link", ""),
            "ats_score":   job.get("ats_score", 0),
            "gaps":        job.get("gaps", ""),
            "tailored":    bool(job.get("tailored", False)),
            "cv_filename": job.get("cv_filename", ""),
            "cv_text":     job.get("cv_text", ""),   # for the history CV preview
            "cv_bucket":   None,
            "cv_path":     None,
        }

        local = job.get("cv_local_path")
        if local and os.path.exists(local):
            with open(local, "rb") as f:
                data = f.read()
            bucket, path = storage_service.upload_file(
                user_id=user_id, run_id=run_id,
                filename=job["cv_filename"], data=data,
                content_type=storage_service.PDF_MIME,
            )
            entry["cv_bucket"] = bucket
            entry["cv_path"] = path
            # Pre-signed link for the spreadsheet (Excel has no auth token).
            job["cv_url"] = storage_service.generate_signed_url(
                bucket, path, storage_service.SPREADSHEET_URL_TTL_SECONDS)

        jobs.append(entry)

    # Build + upload the spreadsheet (now that CV signed URLs exist).
    xlsx_local = os.path.join("outputs", run_id, "jobs.xlsx")
    build_xlsx(job_results, xlsx_local)
    with open(xlsx_local, "rb") as f:
        xlsx_bytes = f.read()
    ss_bucket, ss_path = storage_service.upload_file(
        user_id=user_id, run_id=run_id, filename="jobs.xlsx",
        data=xlsx_bytes, content_type=storage_service.XLSX_MIME,
    )

    _cleanup(run_id)

    return {"jobs": jobs, "spreadsheet_bucket": ss_bucket, "spreadsheet_path": ss_path}


def _cleanup(run_id: str) -> None:
    """Delete the local per-run output dir once everything is in Supabase."""
    d = os.path.join("outputs", run_id)
    shutil.rmtree(d, ignore_errors=True)
