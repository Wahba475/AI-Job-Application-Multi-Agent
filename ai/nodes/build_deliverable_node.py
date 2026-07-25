import os
import re
from ..tools.cv_generator import generate_cv_docx


def cv_filename_for(job) -> str:
    """Canonical CV filename for a job. Strips characters Windows forbids in
    filenames (< > : \" / \\ | ? *) plus whitespace."""
    raw  = f"CV_{job['company']}_{job['title']}"
    safe = re.sub(r'[<>:"/\\|?*\s]+', "_", raw).strip("_")
    return f"{safe}.docx"


def run_dir(run_id: str) -> str:
    """Per-run output directory — isolates concurrent runs so two users never
    overwrite each other's files (the old fixed outputs/ path was a race)."""
    return os.path.join("outputs", run_id)


def build_deliverable_node(state):
    """Generate one .docx per approved CV into outputs/{run_id}/CVs/ and return
    a job_results list for the controller to upload + persist. The spreadsheet
    is built later (in the controller) once CVs are in Supabase, so its links
    can point at the stored files."""
    approved_cvs = state["approved_cvs"]
    run_id = state["run_id"]

    if not approved_cvs:
        print("\n[BUILD] No approved CVs to generate.")
        return {"job_results": []}

    cv_dir = os.path.join(run_dir(run_id), "CVs")
    os.makedirs(cv_dir, exist_ok=True)
    job_results = []

    print(f"\n[BUILD] Generating {len(approved_cvs)} CV file(s) in {cv_dir}...")

    for item in approved_cvs:
        job      = item["job"]
        filename = cv_filename_for(job)
        path     = os.path.join(cv_dir, filename)

        generate_cv_docx(item["cv_text"], path, "")

        job_results.append({
            "title":           job.get("title", ""),
            "company":         job.get("company", ""),
            "location":        job.get("location", ""),
            "employment_type": job.get("employment_type", ""),
            "posted_at":       job.get("posted_at", ""),
            "apply_link":      job.get("apply_link", ""),
            "ats_score":       item.get("ats_score", "N/A"),
            "gaps":            item.get("gaps", ""),
            "tailored":        bool(item.get("tailored", False)),
            "cv_filename":     filename,
            "cv_local_path":   path,
            "cv_text":         item.get("cv_text", ""),
        })
        status = "tailored" if item.get("tailored") else "ORIGINAL(fallback)"
        print(f"  Generated: {filename} (ATS: {item.get('ats_score','N/A')}%, {status})")

    return {"job_results": job_results}
