"""Document and text extraction service for PDF, DOCX, and TXT files."""

import io
import logging
import re
from typing import Optional, Tuple, Union
from app.schemas.document import DocumentSourceType

logger = logging.getLogger(__name__)


# --- Domain Exceptions ---


class DocumentExtractionError(Exception):
    """Base exception for document extraction failures."""
    pass


class UnsupportedDocumentFormatError(DocumentExtractionError):
    """Raised when an uploaded file extension/format is not supported."""
    pass


class EmptyDocumentError(DocumentExtractionError):
    """Raised when an uploaded document contains no content."""
    pass


class NoExtractableTextError(DocumentExtractionError):
    """Raised when a PDF contains no digital text (e.g., scanned/image-only PDF)."""
    pass


class CorruptDocumentError(DocumentExtractionError):
    """Raised when a document is corrupted, damaged, or unreadable."""
    pass


# --- Document Extraction Service ---


class DocumentExtractionService:
    """Service handling text extraction, normalization, and validation across document formats."""

    SUPPORTED_EXTENSIONS = {
        ".pdf": DocumentSourceType.PDF,
        ".docx": DocumentSourceType.DOCX,
        ".txt": DocumentSourceType.TXT,
    }

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize excessive whitespace while preserving paragraph and line structure.

        Args:
            text: Raw input text.

        Returns:
            Cleaned and normalized text string.
        """
        if not text:
            return ""

        # Normalize line endings to LF
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace non-breaking spaces with standard space
        normalized = normalized.replace("\u00a0", " ")

        # Replace horizontal whitespace runs (spaces and tabs) on each line with a single space
        lines = []
        for line in normalized.split("\n"):
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(cleaned_line)

        # Rejoin lines
        rejoined = "\n".join(lines)

        # Collapse 3 or more consecutive newlines down to 2 (preserving standard paragraph break)
        rejoined = re.sub(r"\n{3,}", "\n\n", rejoined)

        return rejoined.strip()

    def extract_from_txt(self, file_bytes: bytes) -> str:
        """Safely decode and extract text from raw TXT bytes.

        Args:
            file_bytes: Raw byte contents of the TXT file.

        Returns:
            Normalized extracted string.

        Raises:
            EmptyDocumentError: If file is empty or contains only whitespace.
            CorruptDocumentError: If text cannot be decoded with standard encodings.
        """
        if not file_bytes or len(file_bytes) == 0:
            raise EmptyDocumentError("The uploaded TXT file is empty (0 bytes).")

        encodings_to_try = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]
        decoded_text: str = ""
        decode_success = False

        for enc in encodings_to_try:
            try:
                decoded_text = file_bytes.decode(enc)
                decode_success = True
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if not decode_success:
            raise CorruptDocumentError("Failed to decode text file. Ensure it is encoded in valid UTF-8.")

        normalized = self.normalize_text(decoded_text)
        if not normalized:
            raise EmptyDocumentError("The uploaded TXT file contains no extractable text.")

        return normalized

    def extract_from_pdf(self, file_bytes: bytes) -> str:
        """Extract extractable text from a digital PDF file using pypdf.

        Args:
            file_bytes: Raw byte contents of the PDF file.

        Returns:
            Normalized extracted text string.

        Raises:
            EmptyDocumentError: If PDF has 0 bytes.
            CorruptDocumentError: If PDF format is invalid or corrupted.
            NoExtractableTextError: If PDF contains no extractable text (e.g. scanned image).
        """
        if not file_bytes or len(file_bytes) == 0:
            raise EmptyDocumentError("The uploaded PDF file is empty (0 bytes).")

        try:
            from pypdf import PdfReader

            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)

            if len(reader.pages) == 0:
                raise EmptyDocumentError("The uploaded PDF contains no pages.")

            extracted_pages = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)

            raw_combined = "\n\n".join(extracted_pages)
            normalized = self.normalize_text(raw_combined)

            if not normalized:
                raise NoExtractableTextError(
                    "No extractable text found in the PDF. Text-based PDF files are required; "
                    "scanned or image-only PDFs without OCR are not supported."
                )

            return normalized

        except (EmptyDocumentError, NoExtractableTextError):
            raise
        except Exception as e:
            logger.error("PDF extraction error: %s", str(e))
            raise CorruptDocumentError(f"Failed to read PDF document. The file may be corrupt or encrypted.") from e

    def extract_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from a DOCX file using python-docx.

        Args:
            file_bytes: Raw byte contents of the DOCX file.

        Returns:
            Normalized extracted text string.

        Raises:
            EmptyDocumentError: If DOCX has 0 bytes or contains no text.
            CorruptDocumentError: If DOCX package is corrupt or invalid.
        """
        if not file_bytes or len(file_bytes) == 0:
            raise EmptyDocumentError("The uploaded DOCX file is empty (0 bytes).")

        try:
            import docx

            stream = io.BytesIO(file_bytes)
            doc = docx.Document(stream)

            content_blocks = []

            # Extract paragraph text
            for p in doc.paragraphs:
                if p.text and p.text.strip():
                    content_blocks.append(p.text.strip())

            # Extract table cell text
            for table in doc.tables:
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text and cell.text.strip()]
                    if row_texts:
                        content_blocks.append(" | ".join(row_texts))

            raw_combined = "\n\n".join(content_blocks)
            normalized = self.normalize_text(raw_combined)

            if not normalized:
                raise EmptyDocumentError("The uploaded DOCX file contains no extractable text.")

            return normalized

        except EmptyDocumentError:
            raise
        except Exception as e:
            logger.error("DOCX extraction error: %s", str(e))
            raise CorruptDocumentError(f"Failed to read DOCX document. The file may be corrupt or invalid.") from e

    def extract_document(self, filename: str, file_bytes: bytes) -> Tuple[str, DocumentSourceType]:
        """Extract and normalize text content from an uploaded document file.

        Args:
            filename: Original filename to determine format.
            file_bytes: Raw file bytes.

        Returns:
            Tuple of (extracted_normalized_text, DocumentSourceType).

        Raises:
            UnsupportedDocumentFormatError: If file extension is unsupported.
            EmptyDocumentError: If document contains no content.
            NoExtractableTextError: If PDF has no digital text.
            CorruptDocumentError: If file is damaged or unreadable.
        """
        if not filename:
            raise UnsupportedDocumentFormatError("Filename is missing.")

        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(self.SUPPORTED_EXTENSIONS.keys()))
            raise UnsupportedDocumentFormatError(
                f"Unsupported document format '{ext}'. Allowed formats: {allowed}"
            )

        source_type = self.SUPPORTED_EXTENSIONS[ext]

        if source_type == DocumentSourceType.PDF:
            text = self.extract_from_pdf(file_bytes)
        elif source_type == DocumentSourceType.DOCX:
            text = self.extract_from_docx(file_bytes)
        elif source_type == DocumentSourceType.TXT:
            text = self.extract_from_txt(file_bytes)
        else:
            raise UnsupportedDocumentFormatError(f"Unsupported format: {source_type}")

        return text, source_type


# Global singleton instance holder for DocumentExtractionService
_document_service_instance: Optional[DocumentExtractionService] = None


def get_document_extraction_service() -> DocumentExtractionService:
    """Retrieve or initialize the global DocumentExtractionService singleton."""
    global _document_service_instance
    if _document_service_instance is None:
        _document_service_instance = DocumentExtractionService()
    return _document_service_instance
