import os
from ..tools.cv_generator import generate_cv_docx
from ..tools.spreadsheet_builder import build_xlsx


def build_deliverable_node(state):
    approved_cvs = state["approved_cvs"]

    if not approved_cvs:
        print("\n[BUILD] No approved CVs to generate.")
        return {}

    os.makedirs("outputs/CVs", exist_ok=True)
    job_results = []

    print(f"\n[BUILD] Generating {len(approved_cvs)} CV file(s)...")

    for item in approved_cvs:
        job      = item["job"]
        filename = f"CV_{job['company']}_{job['title']}.docx"
        filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        path     = f"outputs/CVs/{filename}"

        generate_cv_docx(item["cv_text"], path, "")

        job_results.append({
            "title":           job.get("title", ""),
            "company":         job.get("company", ""),
            "location":        job.get("location", ""),
            "employment_type": job.get("employment_type", ""),
            "posted_at":       job.get("posted_at", ""),
            "apply_link":      job.get("apply_link", ""),
            "ats_score":       item.get("ats_score", "N/A"),
            "cv_path":         path,
        })

        print(f"  Generated: {path} (ATS: {item.get('ats_score', 'N/A')}%)")

    build_xlsx(job_results, "outputs/jobs.xlsx")

    print(f"\n=== Done ===")
    print(f"  CVs:         outputs/CVs/  ({len(job_results)} files)")
    print(f"  Spreadsheet: outputs/jobs.xlsx")

    return {}
