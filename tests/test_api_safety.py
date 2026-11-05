"""API privacy, numerical failure and resource-boundary regressions."""

import asyncio

from fastapi.testclient import TestClient

from app.api.main import PortfolioScenarioRequest, app
from app.api.safety import MAX_REQUEST_BYTES, RequestSafetyMiddleware

client = TestClient(app)
OPTION = dict(S=100, K=100, T=1, r=.05, sigma=.2)
POSITION = {**OPTION, "option_type": "call", "quantity": 1}


def test_validation_does_not_reflect_confidential_input():
    response = client.post('/api/v1/options/price', json={
        **OPTION, 'PRIVATE-RECORD': 'PRIVATE-RECORD', 'S': 'PRIVATE-RECORD'
    })
    assert response.status_code == 422
    assert 'PRIVATE-RECORD' not in response.text
    assert all('input' not in e and 'ctx' not in e for e in response.json()['detail'])


def test_model_validation_does_not_reflect_whole_portfolio():
    response = client.post('/api/v1/portfolio/scenarios', json={
        'positions': [POSITION], 'scenarios': [{'name': 'PRIVATE-RECORD'}] * 2
    })
    assert response.status_code == 422
    assert 'PRIVATE-RECORD' not in response.text


def test_overflow_is_actionable_without_traceback():
    response = client.post('/api/v1/options/price', json={**OPTION, 'r': -1e308})
    assert response.status_code == 422
    assert 'supported numerical' in response.json()['detail']
    assert 'Traceback' not in response.text


def test_nonfinite_calculation_cannot_be_reported_as_valid_price():
    response = client.post('/api/v1/options/batch-price', json={
        'options': [{**OPTION, 'r': -1e308}]
    })
    assert response.status_code == 422


def test_combined_scenario_budget_preserves_normal_calculations():
    import pytest
    from pydantic import ValidationError
    scenarios = [{'name': f's{i}'} for i in range(100)]
    assert len(PortfolioScenarioRequest(positions=[POSITION] * 100,
                                      scenarios=scenarios).positions) == 100
    with pytest.raises(ValidationError, match='10,000 scenario-position'):
        PortfolioScenarioRequest(positions=[POSITION] * 101, scenarios=scenarios)


def test_scenario_name_length_is_bounded():
    response = client.post('/api/v1/portfolio/scenarios', json={
        'positions': [POSITION], 'scenarios': [{'name': 'x' * 81}]
    })
    assert response.status_code == 422


def test_chunked_body_limit_counts_actual_bytes_before_app_runs():
    called = False
    sent = []

    async def downstream(scope, receive, send):
        nonlocal called
        called = True

    chunks = iter([
        {'type': 'http.request', 'body': b'x' * MAX_REQUEST_BYTES, 'more_body': True},
        {'type': 'http.request', 'body': b'x', 'more_body': False},
    ])

    async def receive():
        return next(chunks)

    async def send(message):
        sent.append(message)

    asyncio.run(RequestSafetyMiddleware(downstream)({'type': 'http', 'client': ('127.0.0.1', 1), 'path': '/calculate', 'method': 'POST'}, receive, send))
    assert not called
    assert sent[0]['status'] == 413


def test_sensitive_calculations_and_errors_are_not_cacheable():
    for response in [client.get('/health'),
                     client.post('/api/v1/options/price', json=OPTION),
                     client.post('/api/v1/options/price', json={})]:
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'


def test_optional_api_auth_and_budget_do_not_rely_on_streamlit_sharing():
    from fastapi import FastAPI
    secured = FastAPI()
    secured.add_middleware(RequestSafetyMiddleware, api_token='a' * 32, requests_per_minute=2)

    @secured.get('/health')
    def health():
        return {'status': 'ok'}

    @secured.post('/calculate')
    def calculate():
        return {'value': 1}

    with TestClient(secured) as api:
        assert api.get('/health').status_code == 200
        denied = api.post('/calculate')
        assert denied.status_code == 401
        assert denied.headers['cache-control'] == 'no-store'
        assert api.post('/calculate', headers={'Authorization': 'Bearer wrong'}).status_code == 401
        headers = {'Authorization': 'Bearer ' + 'a' * 32}
        assert api.post('/calculate', headers=headers).status_code == 200
        assert api.post('/calculate', headers=headers).status_code == 200
        throttled = api.post('/calculate', headers=headers)
        assert throttled.status_code == 429
        assert throttled.headers['retry-after'] == '60'
        assert api.get('/health').status_code == 200


def test_short_api_token_fails_instead_of_creating_weak_auth():
    import pytest
    with pytest.raises(ValueError, match='at least 32'):
        RequestSafetyMiddleware(None, api_token='short')
