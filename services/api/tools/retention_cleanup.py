from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.db import db_conn


def main() -> None:
    settings = get_settings()
    print(
        "Retention config:",
        {
            "artifact_days": settings.retention_artifact_days,
            "failed_job_days": settings.retention_failed_job_days,
            "audit_days": settings.retention_audit_days,
        },
    )

    deleted_artifact_files = 0
    deleted_artifact_rows = 0
    deleted_job_rows = 0
    deleted_audit_rows = 0

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, storage_path
                FROM artifacts
                WHERE created_at < NOW() - (%s || ' days')::interval
                """,
                (settings.retention_artifact_days,),
            )
            old_artifacts = cur.fetchall()
            for row in old_artifacts:
                path = Path(row["storage_path"])
                if path.exists() and path.is_file():
                    try:
                        path.unlink()
                        deleted_artifact_files += 1
                    except OSError:
                        pass

            cur.execute(
                """
                DELETE FROM artifacts
                WHERE created_at < NOW() - (%s || ' days')::interval
                """,
                (settings.retention_artifact_days,),
            )
            deleted_artifact_rows = cur.rowcount or 0

            cur.execute(
                """
                DELETE FROM jobs
                WHERE status = 'failed'
                  AND COALESCE(finished_at, queued_at) < NOW() - (%s || ' days')::interval
                """,
                (settings.retention_failed_job_days,),
            )
            deleted_job_rows = cur.rowcount or 0

            cur.execute(
                """
                DELETE FROM audit_events
                WHERE created_at < NOW() - (%s || ' days')::interval
                """,
                (settings.retention_audit_days,),
            )
            deleted_audit_rows = cur.rowcount or 0

    print(
        "Cleanup done:",
        {
            "deleted_artifact_files": deleted_artifact_files,
            "deleted_artifact_rows": deleted_artifact_rows,
            "deleted_failed_jobs": deleted_job_rows,
            "deleted_audit_rows": deleted_audit_rows,
        },
    )


if __name__ == "__main__":
    main()
