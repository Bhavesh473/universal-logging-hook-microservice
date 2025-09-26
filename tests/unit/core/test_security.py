import pytest
from fastapi import HTTPException
from src.core.security import api_key_auth
import os

def test_api_key_auth_valid(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_key")
    assert api_key_auth(x_api_key="test_key") == "test_key"

def test_api_key_auth_invalid(monkeypatch):
    monkeypatch.setenv("API_KEY", "test_key")
    with pytest.raises(HTTPException) as exc:
        api_key_auth(x_api_key="wrong_key")
    assert exc.value.status_code == 403 