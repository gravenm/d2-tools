import logging
import colorlog
from core.constants import *
import streamlit as st
import sqlite3
import json

# --- Logger Setup ---
def setup_logger():
    """Sets up a colored logger."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s %(message)s',
            log_colors={
                'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow',
                'ERROR': 'red', 'CRITICAL': 'bold_red',
            }
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def item_hash_to_id(item_hash):
    return item_hash if item_hash < 2**31 else item_hash - 2**32

def initialize_session_state():
    if 'weights_initialized' not in st.session_state:
        st.session_state.weights = DEFAULT_WEIGHTS.copy()
        st.session_state.archetype_weights = ARCHETYPE_WEIGHTS.copy()
        st.session_state.tier_weights = {
            tier: {**values, 'enabled': True} for tier, values in TIER_WEIGHTS.items()
        }
        st.session_state.illegal_combo_weights = ILLEGAL_COMBO_WEIGHTS.copy()        
        st.session_state.weights_initialized = True

def query_manifest(_db_path, table_name, item_hash):
    try:
        with sqlite3.connect(_db_path) as con:
            cur = con.cursor()
            cur.execute(f"SELECT json FROM {table_name} WHERE id = ?", (item_hash_to_id(item_hash),))
            result = cur.fetchone()
            if result: return json.loads(result[0])
    except Exception as e: st.error(f"Database error querying {table_name}: {e}")
    return None        