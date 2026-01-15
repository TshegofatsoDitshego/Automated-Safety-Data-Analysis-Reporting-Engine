from src.processing.validators import validate_event
from src.processing.transformers import enrich_event
from src.storage.database import save_event
from src.utils.logger import get_logger

logger = get_logger(__name__)

def ingest_event(event: dict) -> None:
    validated = validate_event(event)
    enriched = enrich_event(validated)
    save_event(enriched)
    logger.info("Event ingested successfully")
