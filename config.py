from pathlib import Path
import logging, logging.config, logging.handlers

# --- DIRS ---

BASE_DIR = Path(__file__).parent
CERT_DIR = BASE_DIR / "cert"
DATA_DIR = BASE_DIR / "data"
XLS_HISTORY_DIR = DATA_DIR / "xls_files_history"
SCRAPER_DIR = BASE_DIR / "scraper"
HTMLS_DIR = DATA_DIR / "htmls"
TESTS_DIR = BASE_DIR / "tests"

# --- PATHS ---

CERT_PATH = CERT_DIR / "bcv_org.pem"
DEBUGGING_BASE_INDEX_PATH = HTMLS_DIR / "index.html" # html base
DEBUGGING_XLS_INDEX_PATH = HTMLS_DIR / "links_index.html" # Página con los links, tiene paginación

URL_BASE = "https://www.bcv.org.ve/"
URL_WITH_XLS_FILES = "https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc"

# --- PARSER SELECTORS ---

FECHA_VALOR_DOLAR_SELECTOR = "div.pull-right.dinpro.center span.date-display-single[content]"
DOLAR_RATE_SELECTOR = "div#dolar strong.strong-tb"
TABLE_SELECTOR = "div.view-content > table.views-table.cols-2.table.table-0"

# DEBE SER USADO EN EL TAG "TABLE"
LINK_SELECTOR = "tbody tr span.file a[href$='.xls']" # revisar validez
# content="2026-06-09T00:00:00-04:00"
# --- ISOFORMAT REGEX PATTER ---
ISOFORMAT_PATTERN = (
    r"^\d{4}-\d{2}-\d{2}"
    r"T\d{2}:\d{2}:\d{2}"
    r"[+-]\d{2}:\d{2}$"
)

# --- LOGGING DICTCONFIG ---
dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{"
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple" 
        }
    },

    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG"
        }
    }
}

def setup_logging_config():
    logging.config.dictConfig(dict_config)