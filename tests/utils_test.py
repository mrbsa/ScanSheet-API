import base64
import json
import pytest
from fastapi import HTTPException
from PIL import Image
import io
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from api.utils import encryption, img_merger, pdf_generator

# Auxiliary
def make_base64_image(color=(255, 0, 0), size=(50, 50)) -> str:  # encoded jpeg image
    img = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# Tests (encryption.py)
def test_encrypt_and_decrypt_roundtrip():
    key = AESGCM.generate_key(bit_length=128)
    key_b64 = base64.b64encode(key).decode()
    data = {"foo": "bar"}

    encrypted = encryption.encrypt(data, key_b64)
    assert isinstance(encrypted, str)

    decrypted = encryption.decrypt(encrypted, key_b64)
    assert decrypted == data

def test_encrypt_invalid_key():
    with pytest.raises(HTTPException) as excinfo:
        encryption.encrypt({"foo": "bar"}, "invalid_key")
    assert excinfo.value.status_code == 500
    assert "error" in excinfo.value.detail

def test_decrypt_invalid_payload():
    key = AESGCM.generate_key(bit_length=128)
    key_b64 = base64.b64encode(key).decode()

    with pytest.raises(HTTPException) as excinfo:
        encryption.decrypt("not_base64", key_b64)
    assert excinfo.value.status_code == 500
    assert "error" in excinfo.value.detail

# Tests (img_merger.py)
def test_merge_base64_images_success():
    img1 = make_base64_image(color=(255, 0, 0), size=(10, 10))
    img2 = make_base64_image(color=(0, 255, 0), size=(10, 20))

    merged_b64 = img_merger.merge_base64_images([img1, img2])
    assert isinstance(merged_b64, str)

    merged_bytes = base64.b64decode(merged_b64)
    merged_img = Image.open(io.BytesIO(merged_bytes))
    assert merged_img.size[1] == 30  # verify image dimensions 

def test_merge_base64_images_with_invalid_image():
    bad_img = "not_base64"
    good_img = make_base64_image()

    result = img_merger.merge_base64_images([bad_img, good_img])
    assert isinstance(result, str) 

def test_merge_base64_images_empty_list():
    assert img_merger.merge_base64_images([]) is None

# Tests (pdf_generator.py)
def test_image_to_pdf_success():
    img_b64 = make_base64_image()
    pdf_b64 = pdf_generator.image_to_pdf(img_b64)
    assert isinstance(pdf_b64, str)
    assert base64.b64decode(pdf_b64).startswith(b"%PDF")  # PDF magic number

def test_image_to_pdf_failure():
    with pytest.raises(HTTPException) as excinfo:
        pdf_generator.image_to_pdf("not_base64")
    assert excinfo.value.status_code == 500
    assert "Failed to convert image to pdf" in excinfo.value.detail

def test_images_to_pdf_success():
    imgs_b64 = [make_base64_image(), make_base64_image()]
    pdf_b64 = pdf_generator.images_to_pdf(imgs_b64)
    assert isinstance(pdf_b64, str)
    assert base64.b64decode(pdf_b64).startswith(b"%PDF")

def test_images_to_pdf_empty_list():
    with pytest.raises(HTTPException) as excinfo:
        pdf_generator.images_to_pdf([])
    assert excinfo.value.status_code == 500
    assert "Failed to convert images to pdf" in excinfo.value.detail

def test_images_to_pdf_invalid_image():
    with pytest.raises(HTTPException):
        pdf_generator.images_to_pdf(["not_base64"])
