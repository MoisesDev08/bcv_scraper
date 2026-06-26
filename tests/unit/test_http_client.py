from urllib.parse import parse_qs, urlparse

import pytest
import responses

from bcv.scraper.exceptions import RetryableError


def test_prove_fake_useragent_works(client_instance):

    UserAgent = client_instance.ua
    ua = UserAgent.random

    assert ua is not None
    assert len(ua) > 0


def test_user_agent_fallback(monkeypatch, client_instance):

    current_ua_from_fallback = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
    )

    monkeypatch.setattr(client_instance, "ua", None)
    ua_gotten = client_instance._get_user_agent()
    ua_expected = client_instance._fallback_user_agent_helper()

    assert ua_gotten == ua_expected
    assert ua_gotten == current_ua_from_fallback


@pytest.mark.parametrize(
    "k, pttr_expected",
    [
        ("accept", r"(text/html|application)+"),
        ("accept-language", r"(en-us|es-[mxesus])+"),
        ("referer", r"(^https?://)(www.)*"),
        ("user-agent", ""),
    ],
)
def test_check_headers(client_instance, k, pttr_expected, ua_patterns):

    import re

    headers = client_instance._get_headers()
    resultado = headers.get(k, None)

    def func_match(pttr, string):
        re.search(pttr, string, re.IGNORECASE)

    if k == "user-agent":
        list_pttr_expected = ua_patterns
        for pttr in list_pttr_expected:
            match = func_match(pttr, resultado)
            if match is not None:
                break

    else:
        match = bool(func_match(pttr_expected, resultado))

    if match is None:
        from ua_parser import user_agent_parser

        parsed = user_agent_parser.Parse(resultado)
        match = parsed["user_agent"]["family"] not in (None, "Other")

    assert resultado is not None
    assert match


def test_prove_fetch_bcv_url_if_not_given(client_instance, rsps):
    rsps.add(
        url="https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc",
        method=responses.GET,
    )

    response = client_instance.fetch()
    assert (
        response.url
        == "https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc"
    )
    assert response.status_code == 200


def test_prove_fetch_bcv_url_if_given(client_instance, rsps):
    rsps.add(url="https://www.http.org.bin/fake-url-for-test", method=responses.GET)

    response = client_instance.fetch(url="https://www.http.org.bin/fake-url-for-test")
    assert response.url == "https://www.http.org.bin/fake-url-for-test"
    assert response.status_code == 200


def test_prove_fetch_params_and_page_exclusive_args(
    client_instance, rsps_without_assert
):

    rsps_without_assert.add(
        url="https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc",
        method=responses.GET,
    )

    with pytest.raises(AttributeError) as AtErr:
        client_instance.fetch(params={"foo": "bar"}, page=0)
        assert "Don't use params and page at the same time." in str(AtErr.value)


def test_prove_fetch_page_param_construction(client_instance, rsps):

    rsps.add(
        method=responses.GET,
        url="https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc?page=0",
    )
    response = client_instance.fetch(page=0)
    parsed = urlparse(response.url)
    parsed_qs = parse_qs(parsed.query)

    assert parsed_qs["page"][0] == "0"


@pytest.mark.parametrize(
    "status_code, attemps", [(408, 1), (429, 2), (500, 3), (502, 4), (503, 5), (504, 1)]
)
def test_prove_retry_if_status_code_is_retryable_work_and_attemps(
    client_instance, rsps_without_assert, mocker, status_code, attemps
):

    from tenacity import RetryError, stop_after_attempt, wait_none

    rsps_without_assert.add(
        method=responses.GET,
        url="https://www.bcv.org.ve/estadisticas/tipo-cambio-de-referencia-smc",
        status=status_code,
    )

    spy = mocker.spy(client_instance, "_do_request")
    client_instance.fetch.retry.stop = stop_after_attempt(attemps)
    client_instance.fetch.retry.wait = wait_none()

    with pytest.raises((RetryableError, RetryError)):
        client_instance.fetch()

    assert spy.call_count == attemps
