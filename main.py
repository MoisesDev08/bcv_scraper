import config as cf
from scraper.http_client import HttpClient

def main():
    cf.setup_logging_config()
    client = HttpClient()
    for page in range(0, 8):
        print(client.fetch(page))