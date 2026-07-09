"""Supabase Storage helpers.

HOW STORAGE WORKS (the mental model you asked about):
  - A bucket ("deliverables") holds arbitrary files — .docx, .xlsx, anything.
  - Every file lives at a PATH inside the bucket. We namespace by user + run:
        deliverables/{user_id}/{run_id}/CV_Company_Title.docx
        deliverables/{user_id}/{run_id}/jobs.xlsx
    so each user's files are grouped and a whole run is easy to find/delete.
  - Upload:  storage.from_(bucket).upload(path, bytes)
  - Because the bucket is PRIVATE, files aren't public. To let a user download,
    we mint a SIGNED URL — a temporary link (expires) that grants read access
    to exactly that one object. We store that URL in the DB row.

CONNECTING TO THE SCHEMA:
  upload_deliverable() returns the signed URL. The pipeline saves it into the
  `runs` row: the spreadsheet URL in `spreadsheet_url`, and each CV URL inside
  the `jobs` JSONB array (job["cv_url"]). That's the whole link: DB row → URL →
  file in the bucket.
"""
import os
from db.supabase_client import get_supabase

BUCKET = os.getenv("SUPABASE_BUCKET", "deliverables")

# Signed URLs live for 7 days — long enough for a user to come back to their
# history and re-download, short enough that a leaked link eventually dies.
SIGNED_URL_TTL_SECONDS = 7 * 24 * 3600


def upload_deliverable(user_id: str, run_id: str, filename: str, data: bytes,
                       content_type: str) -> str:
    """Upload one file to deliverables/{user_id}/{run_id}/{filename} and return
    a signed download URL. Overwrites if the same path already exists."""
    sb = get_supabase()
    path = f"{user_id}/{run_id}/{filename}"
    store = sb.storage.from_(BUCKET)

    store.upload(
        path=path,
        file=data,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    signed = store.create_signed_url(path, SIGNED_URL_TTL_SECONDS)
    # supabase-py returns {"signedURL": "..."} (or signed_url on some versions)
    return signed.get("signedURL") or signed.get("signed_url", "")


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
