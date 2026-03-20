"""
Google Document AI service for gazette PDF parsing.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentAIService:
    """Service for parsing gazette PDFs with Google Document AI."""

    def __init__(self) -> None:
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = "us"
        self.processor_id = settings.DOCUMENT_AI_PROCESSOR_ID
        self._client: Any = None
        self._documentai: Any = None
        self._processor_name: str | None = None

    def _ensure_client(self) -> None:
        if self._client is not None:
            return

        if not self.project_id or not self.processor_id:
            raise RuntimeError("Document AI is not configured")

        try:
            from google.api_core.client_options import ClientOptions
            from google.cloud import documentai_v1 as documentai
            from google.oauth2 import service_account
        except ImportError as exc:
            raise RuntimeError("google-cloud-documentai is not installed") from exc

        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        credentials = None
        if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
                credentials = service_account.Credentials.from_service_account_info(info)
            except Exception as exc:
                raise RuntimeError("Invalid GOOGLE_SERVICE_ACCOUNT_JSON configuration") from exc
        elif settings.GOOGLE_APPLICATION_CREDENTIALS_PATH:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_APPLICATION_CREDENTIALS_PATH
                )
            except Exception as exc:
                raise RuntimeError(
                    "Invalid GOOGLE_APPLICATION_CREDENTIALS_PATH configuration"
                ) from exc

        try:
            self._client = documentai.DocumentProcessorServiceClient(
                client_options=opts,
                credentials=credentials,
            )
        except Exception as exc:
            message = str(exc)
            if "default credentials were not found" in message.lower():
                raise RuntimeError(
                    "Document AI credentials are missing. Configure "
                    "GOOGLE_APPLICATION_CREDENTIALS_PATH or GOOGLE_SERVICE_ACCOUNT_JSON."
                ) from exc
            raise
        self._documentai = documentai
        self._processor_name = self._client.processor_path(
            self.project_id,
            self.location,
            self.processor_id,
        )

    async def parse_gazette_pdf(
        self,
        pdf_bytes: bytes,
        mime_type: str = "application/pdf",
    ) -> dict[str, Any]:
        """Parse a gazette PDF and return text/table extraction."""
        self._ensure_client()
        assert self._documentai is not None
        assert self._processor_name is not None

        request = self._build_process_request(pdf_bytes, mime_type=mime_type, imageless_mode=True)

        try:
            result = await asyncio.to_thread(self._client.process_document, request=request)
            document = result.document
            full_text = document.text or ""
            tables = self._extract_tables(document, full_text)
            confidence = self._calculate_confidence(document)

            return {
                "text": full_text,
                "tables": tables,
                "pages": len(document.pages),
                "confidence": confidence,
            }
        except Exception as exc:
            logger.exception("Document AI processing failed")
            raise RuntimeError(f"Failed to parse gazette PDF: {exc}") from exc

    def _build_process_request(
        self,
        pdf_bytes: bytes,
        *,
        mime_type: str,
        imageless_mode: bool,
    ) -> Any:
        assert self._documentai is not None
        assert self._processor_name is not None

        raw_document = self._documentai.RawDocument(content=pdf_bytes, mime_type=mime_type)
        request_kwargs: dict[str, Any] = {
            "name": self._processor_name,
            "raw_document": raw_document,
        }

        process_options_cls = getattr(self._documentai, "ProcessOptions", None)
        if process_options_cls is not None:
            try:
                process_options = process_options_cls()
                if imageless_mode and hasattr(process_options, "imageless_mode"):
                    setattr(process_options, "imageless_mode", True)
                request_kwargs["process_options"] = process_options
            except Exception:
                logger.warning("Unable to configure Document AI process_options", exc_info=True)

        try:
            return self._documentai.ProcessRequest(**request_kwargs)
        except TypeError:
            logger.warning("Document AI request options unsupported; retrying without options")
            return self._documentai.ProcessRequest(
                name=self._processor_name,
                raw_document=raw_document,
            )

    def _extract_tables(self, document: Any, full_text: str) -> list[dict[str, Any]]:
        tables: list[dict[str, Any]] = []
        for page in getattr(document, "pages", []):
            for table in getattr(page, "tables", []):
                headers: list[str] = []
                if getattr(table, "header_rows", []):
                    for cell in table.header_rows[0].cells:
                        headers.append(self._get_text(cell.layout, full_text).strip())

                rows: list[dict[str, Any]] = []
                for row in getattr(table, "body_rows", []):
                    row_data: dict[str, Any] = {}
                    for idx, cell in enumerate(getattr(row, "cells", [])):
                        key = (
                            headers[idx] if idx < len(headers) and headers[idx] else f"Column {idx}"
                        )
                        row_data[key] = self._get_text(cell.layout, full_text).strip()
                    if row_data:
                        rows.append(row_data)

                if headers and rows:
                    tables.append({"headers": headers, "rows": rows})
        return tables

    def _get_text(self, layout: Any, full_text: str) -> str:
        text = ""
        anchor = getattr(layout, "text_anchor", None)
        if anchor is None:
            return text
        for segment in getattr(anchor, "text_segments", []):
            start_index = int(segment.start_index) if getattr(segment, "start_index", None) else 0
            end_index = (
                int(segment.end_index) if getattr(segment, "end_index", None) else len(full_text)
            )
            text += full_text[start_index:end_index]
        return text

    def _calculate_confidence(self, document: Any) -> float:
        confidences: list[float] = []
        for page in getattr(document, "pages", []):
            for table in getattr(page, "tables", []):
                for row in getattr(table, "body_rows", []):
                    for cell in getattr(row, "cells", []):
                        conf = getattr(cell.layout, "confidence", None)
                        if conf is not None:
                            confidences.append(float(conf))
        if confidences:
            return sum(confidences) / len(confidences)
        return 0.0


document_ai_service = DocumentAIService()
