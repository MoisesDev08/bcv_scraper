from pathlib import Path

# --- DIRS ---
ROOT_DIR = Path(__file__).parent.parent
BCV_DIR = ROOT_DIR / "bcv"
CERT_DIR = ROOT_DIR / "cert"
DATA_DIR = ROOT_DIR / "data"
XLS_HISTORY_DIR = DATA_DIR / "xls_files_history"
SCRAPER_DIR = BCV_DIR / "scraper"

TESTS_DIR = ROOT_DIR / "tests"
TESTS_HELPERS_DIR = TESTS_DIR / "helpers"
TESTS_FIXTURES_DIR = TESTS_DIR / "fixtures"
TESTS_INTEGRATION_DIR = TESTS_DIR / "integration"
TESTS_UNIT_DIR = TESTS_DIR / "unit"

TESTS_SAMPLES_DIR = TESTS_DIR / "samples"
TESTS_SAMPLES_HTML_DIR = TESTS_SAMPLES_DIR / "html"
TESTS_SAMPLES_JSON_DIR = TESTS_SAMPLES_DIR / "json"
TESTS_SAMPLES_XLS_DIR = TESTS_SAMPLES_DIR / "xls"


# --- PATHS ---

CERT_PATH = CERT_DIR / "bcv_org.pem"
DEBUGGING_BASE_INDEX_PATH = ...
DEBUGGING_XLS_INDEX_PATH = ...

URL_BASE = "https://www.bcv.org.ve/"
URL_WITH_XLS_FILES = "https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc"

# --- PARSER SELECTORS ---

FECHA_VALOR_DOLAR_SELECTOR = (
    "div.pull-right.dinpro.center span.date-display-single[content]"
)
DOLAR_RATE_SELECTOR = "div#dolar strong.strong-tb"
TABLE_SELECTOR = "div.view-content > table.views-table.cols-2.table.table-0"

# DEBE SER USADO EN EL TAG "TABLE"
LINK_SELECTOR = "span.file a[href$='.xls']"
NEXT_PAGE_SELECTOR = "div.text-center ul.pagination li.next a"

# --- ISOFORMAT REGEX PATTER ---
ISOFORMAT_PATTERN = (
    r"^\d{4}-\d{2}-\d{2}"
    r"T\d{2}:\d{2}:\d{2}"
    r"[+-]\d{2}:\d{2}$"
)

# --- XLS PARSER PATTERNS ---
# DEBEN SER USADOS CON INSENSITIVE CASE/IGNORE CASE

FECHA_VALOR_PATTERN_XLS_ROW = r"(?:valor)[:\s]*(?:\d{2}/\d{2}/\d{4}[\s]*)"
FECHA_OPER_PATTERN_XLS_ROW = r"(?:operaci[oó]n)[:\s]*(?:\d{2}/\d{2}/\d{4}[\s]*)"
TASA_DOLAR_PATTERN_XLS_ROW = r"(?:usd|e[/.]*u[/.]*a[/.\s]*)"

# --- LOGGING DICTCONFIG ---
dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        }
    },
    "loggers": {"": {"handlers": ["console"], "level": "DEBUG"}},
}
