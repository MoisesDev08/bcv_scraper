from bcv.scraper.http_client import HttpClient
import pytest
import responses

@pytest.fixture
def client_instance():
    return HttpClient()

@pytest.fixture
def ua_patterns():
    return [
        # Chrome Desktop
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Safari/\d+\.\d+$',

        # Chrome Mobile (Android)
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Mobile Safari/\d+\.\d+$',

        # Chrome iOS (CriOS)
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) CriOS/\d+\.\d+\.\d+\.\d+ Mobile/\w+ Safari/\d+\.\d+$',

        # Safari iOS
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Version/\d+\.\d+(\.\d+)? Mobile/\w+ Safari/\d+\.\d+$',

        # Safari macOS
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Version/\d+\.\d+ Safari/\d+\.\d+$',

        # Edge Chromium
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Safari/\d+\.\d+ Edg/\d+\.\d+\.\d+\.\d+$',

        # Opera Chromium
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Safari/\d+\.\d+ OPR/\d+\.\d+\.\d+\.\d+$',

        # Firefox Desktop
        r'^Mozilla/5\.0 \([^)]+; rv:\d+\.\d+\) Gecko/\d+ Firefox/\d+\.\d+$',

        # Android WebView
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Version/\d+\.\d+ Chrome/\d+\.\d+\.\d+\.\d+ Mobile Safari/\d+\.\d+$',

        # Samsung Internet
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) SamsungBrowser/\d+\.\d+ Chrome/\d+\.\d+\.\d+\.\d+ Mobile Safari/\d+\.\d+$',
        
        # Yandex Browser
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) YaBrowser/\d+\.\d+\.\d+\.\d+ Chrome/\d+\.\d+\.\d+\.\d+ Safari/\d+\.\d+$',

        # DuckDuckGo iOS
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) DuckDuckGo/\d+\.\d+ Mobile/\w+ Safari/\d+\.\d+$',

        # DuckDuckGo Android
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ DuckDuckGo/\d+\.\d+ Mobile Safari/\d+\.\d+$',

        # Brave Browser
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Safari/\d+\.\d+ Brave/\d+\.\d+$',

        # Vivaldi
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Safari/\d+\.\d+ Vivaldi/\d+\.\d+\.\d+\.\d+$',

        # Opera Mobile
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Chrome/\d+\.\d+\.\d+\.\d+ Mobile Safari/\d+\.\d+ OPR/\d+\.\d+\.\d+\.\d+$',

        # Firefox iOS
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) FxiOS/\d+\.\d+ Mobile/\w+ Safari/\d+\.\d+$',

        # WebView iOS
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) Mobile/\w+ Safari/\d+\.\d+$',

        # POSITIVOS AÑADIDOS COMO PARCHE
        r'^Mozilla/5\.0 \([^)]+\) AppleWebKit/\d+\.\d+ \(KHTML, like Gecko\) GSA/\d+.\d+ Mobile/\w+ Safari/\d+\.\d+$'

        # FALSOS POSITIVOS NO INCLUIDOS POR EL PATRÓN
        #'Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Mobile/15E148 Safari/604.1'
        #'Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/363.0.743255906 Mobile/15E148 Safari/604.1'
    ]

@pytest.fixture
def rsps():
    with responses.RequestsMock() as rsps:
        yield rsps

@pytest.fixture
def rsps_without_assert():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps