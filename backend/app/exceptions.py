"""Domain exceptions raised by the analysis pipeline."""


class AuditorError(Exception):
    """Base class for all auditor domain errors."""


class FileValidationError(AuditorError):
    """An uploaded file failed type or size validation."""


class PDFExtractionError(AuditorError):
    """A purchase order PDF could not be read or contained no text."""


class LLMParsingError(AuditorError):
    """The LLM response was missing, malformed, or failed schema validation."""


class CatalogValidationError(AuditorError):
    """The product catalog CSV is missing required columns or usable rows."""
