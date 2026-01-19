"""
Minimal Supabase integration for the AI Resume & Career Assistant.

This service is intentionally simple and production-inspired:
- Reads credentials from environment variables
- Provides small helper methods for inserts and file uploads
- Fails gracefully (no-op) when Supabase is not configured
- Uses direct HTTP calls to avoid Rust dependencies
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    import httpx
    http_client_available = True
except ImportError:
    http_client_available = False


class SupabaseService:
    """Thin wrapper around Supabase HTTP API for this MVP."""

    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.api_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        self._enabled = bool(self.url and self.api_key and http_client_available)
        self._client = None

        if self._enabled:
            try:
                self._client = httpx.Client(
                    base_url=self.url,
                    headers={
                        "apikey": self.api_key,
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
            except Exception:
                # If configuration fails, keep service as disabled
                self._enabled = False
                self._client = None

    @property
    def is_enabled(self) -> bool:
        """Return True when Supabase is correctly configured."""
        return bool(self._enabled and self._client is not None)

    # ---------- Authentication (placeholder) ----------
    def authenticate_user(self, user_id: str) -> Dict[str, Any]:
        """
        MVP-level auth placeholder.

        In a real system, we'd validate tokens or session.
        Here we simply return a lightweight user object so the
        rest of the pipeline can assume a "user" exists.
        """
        return {"id": user_id}

    # ---------- Data persistence helpers ----------
    def save_chatbot_answers(
        self,
        session_id: str,
        answers: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> None:
        """Persist raw chatbot answers for a resume session."""
        if not self.is_enabled:
            return

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "answers": answers,
            "source": "chatbot",
        }

        try:
            response = self._client.post("/rest/v1/chatbot_answers", json=payload)
            response.raise_for_status()
        except Exception:
            # Fail silently in this MVP to avoid breaking the flow
            return

    def save_resume_results(
        self,
        session_id: str,
        resume_json: Dict[str, Any],
        score: int,
        skill_gaps: Optional[list[str]] = None,
        career_roadmap: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Store AI workflow outputs:
        - structured resume JSON
        - resume score
        - skill gaps
        - career roadmap
        """
        if not self.is_enabled:
            return

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "resume_json": resume_json,
            "resume_score": score,
            "skill_gaps": skill_gaps or [],
            "career_roadmap": career_roadmap or {},
        }

        try:
            response = self._client.post("/rest/v1/resume_results", json=payload)
            response.raise_for_status()
        except Exception:
            return

    # ---------- File storage helpers ----------
    def save_resume_file(
        self,
        session_id: str,
        file_path: str,
        content_type: str,
        bucket: str = "resumes",
    ) -> Optional[str]:
        """
        Upload generated resume file (PDF / DOCX) to Supabase Storage.

        Returns the public path (if available) or None on failure.
        """
        if not self.is_enabled or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            file_name = os.path.basename(file_path)
            storage_path = f"{session_id}/{file_name}"

            # Upload file
            self._client.storage.from_(bucket).upload(  # type: ignore[union-attr]
                file=storage_path,
                file_content=file_bytes,
                file_options={"content-type": content_type},
            )

            # Try to create a public URL (if the bucket is public)
            try:
                res = self._client.storage.from_(bucket).get_public_url(storage_path)  # type: ignore[union-attr]
                return getattr(res, "public_url", None) if res is not None else None
            except Exception:
                return storage_path
        except Exception:
            return None

