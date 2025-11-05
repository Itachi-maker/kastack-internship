import sys
import logging
from etl_pipeline import run_etl

# Configure logging for the main script
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('root')

if __name__ == "__main__":
    try:
        run_etl()
        sys.exit(0)  # Explicitly exit with success code
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        sys.exit(1)  # Explicitly exit with failure code
