# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

# Global simulation config
DEFAULT_SCENARIO_ID = os.getenv("DEFAULT_SCENARIO_ID", "S1")
PRICE_PER_UNIT = float(os.getenv("DEFAULT_PRICE_PER_UNIT", "1.00"))
OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "outputs/reports")
LOG_LEVEL = os.getenv("STREAMLIT_LOG_LEVEL", "info")
