import pytest
from unittest.mock import Mock

from fastapi.testclient import TestClient

from main import app
from dependencies import (
    get_opa_rule_service,
    get_exchange_rate_service,
)


@pytest.fixture
def mock_opa_service():
    return Mock()


@pytest.fixture
def mock_rate_service():
    return Mock()


@pytest.fixture
def client(
    mock_opa_service,
    mock_rate_service,
):

    app.dependency_overrides[
        get_opa_rule_service
    ] = lambda: mock_opa_service

    app.dependency_overrides[
        get_exchange_rate_service
    ] = lambda: mock_rate_service

    yield TestClient(app)

    app.dependency_overrides.clear()
