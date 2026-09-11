import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from a2a_sdk.client import A2AGatewayClient

def test_a2a_sdk_health():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    health = client.health()
    assert "option1" in health
    assert "option2" in health

def test_a2a_sdk_agent_card():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    card = client.get_agent_card()
    assert "A2A" in card["name"]
    assert "declaredSkills" in card
    assert "capabilities" in card

def test_a2a_sdk_a2ui_templates():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    templates = client.get_a2ui_templates()
    assert "templates" in templates
    assert "dose_titration" in templates["templates"]

def test_a2a_sdk_kpi_benchmarks():
    client = A2AGatewayClient(base_url="http://127.0.0.1:8090")
    kpis = client.get_kpi_benchmarks()
    assert "metrics" in kpis
