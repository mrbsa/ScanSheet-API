import sys
import os
import types
import pytest
from unittest.mock import patch, MagicMock

# Add route to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set mock .env variables
os.environ["AUTH_TOKEN"] = "test_token"
os.environ["SYMMETRIC_KEY"] = "test_key"
os.environ["GPT_API_KEY"] = "fake_gpt_key"
os.environ["MISTRAL_API_KEY"] = "fake_mistral_key"

# Mock utils
fake_utils = types.ModuleType("utils")
fake_pdf_generator = types.ModuleType("utils.pdf_generator")
fake_encryption = types.ModuleType("utils.encryption")
fake_img_merger = types.ModuleType("utils.img_merger")

fake_pdf_generator.image_to_pdf = lambda img: "fake_pdf"
fake_pdf_generator.images_to_pdf = lambda imgs: "fake_pdf"
fake_encryption.encrypt = lambda data, key: "encrypted_result"
fake_encryption.decrypt = lambda payload, key: {"image_bytes": ["fake_img"], "title": "test"}
fake_img_merger.merge_base64_images = lambda imgs: "merged_img"

sys.modules["utils"] = fake_utils
sys.modules["utils.pdf_generator"] = fake_pdf_generator
sys.modules["utils.encryption"] = fake_encryption
sys.modules["utils.img_merger"] = fake_img_merger

# Import mocked app
from fastapi.testclient import TestClient
from api import app as app_module

app = app_module.app
client = TestClient(app)

# Mock agent
@pytest.fixture(autouse=True)
def mock_agent():
    with patch.object(app_module, "agent", MagicMock(run=lambda variables: {"result": "ok"})):
        yield

# Tests
def test_unauthorized():
    resp = client.post("/process-image", headers={"Authorization": "wrong_token"}, json={"payload": "data"})
    assert resp.status_code == 401
    assert "Unauthorized" in resp.text

def test_no_images(monkeypatch):
    monkeypatch.setattr(app_module, "decrypt", lambda payload, key: {"image_bytes": [], "title": "x"})
    resp = client.post("/process-image", headers={"Authorization": "test_token"}, json={"payload": "data"})
    assert resp.status_code == 400
    assert "'image_bytes' must be a list" in resp.text

def test_success_single_doc(monkeypatch):
    monkeypatch.setattr(app_module, "decrypt", lambda p, k: {"image_bytes": ["img1"], "title": "ficha_cadastro_individual"})
    resp = client.post("/process-image", headers={"Authorization": "test_token"}, json={"payload": "x"})
    assert resp.status_code == 200
    assert resp.json()["table"] == "encrypted_result"

def test_success_multiple_images(monkeypatch):
    monkeypatch.setattr(app_module, "decrypt", lambda p, k: {"image_bytes": ["img1", "img2"], "title": "something"})
    resp = client.post("/process-image", headers={"Authorization": "test_token"}, json={"payload": "x"})
    assert resp.status_code == 200
    assert resp.json()["table"] == "encrypted_result"

def test_agent_failure(monkeypatch):
    monkeypatch.setattr(app_module, "agent", MagicMock(run=lambda variables: (_ for _ in ()).throw(Exception("fail"))))
    resp = client.post("/process-image", headers={"Authorization": "test_token"}, json={"payload": "x"})
    assert resp.status_code == 500
    assert "Agent error" in resp.text
