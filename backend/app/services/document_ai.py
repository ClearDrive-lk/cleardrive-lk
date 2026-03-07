"""
Google Document AI service for gazette PDF parsing.
"""

from __future__ import annotations

import asyncio
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
        except ImportError as exc:
            raise RuntimeError("google-cloud-documentai is not installed") from exc

        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self._client = documentai.DocumentProcessorServiceClient(client_options=opts)
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

        raw_document = self._documentai.RawDocument(content=pdf_bytes, mime_type=mime_type)
        request = self._documentai.ProcessRequest(
            name=self._processor_name,
            raw_document=raw_document,
        )

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
