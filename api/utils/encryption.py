from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException
import base64
import json
import logging
import os

# Configure server logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("encryption_utils")

def decrypt(encrypted_payload: str, decryption_key_b64: str) -> dict:
    try:
        decoded_payload = base64.b64decode(encrypted_payload)  # decode request payload
        nonce = decoded_payload[:12]  # 12-byte nonce
        ciphertext = decoded_payload[12:-16]
        tag = decoded_payload[-16:]

        decryption_key = base64.b64decode(decryption_key_b64)  # decode encryption key
        aesgcm = AESGCM(decryption_key)
        decrypted = aesgcm.decrypt(nonce, ciphertext + tag, None)

        return json.loads(decrypted)  # return raw payload
    
    except Exception as e:
        logger.info("ERROR: Decryption failed.")
        raise HTTPException(status_code=500, detail={"error": str(e)})


def encrypt(raw_data: dict, encryption_key_b64: str) -> str:
    try:
        encryption_key = base64.b64decode(encryption_key_b64)  # decode enryption key
        aesgcm = AESGCM(encryption_key)
        nonce = os.urandom(12)
        json_data = json.dumps(raw_data).encode()  # turn raw data into bytes (encryption only works for bytes)

        encrypted = aesgcm.encrypt(nonce, json_data, None)  # re-encrypts

        return base64.b64encode(nonce + encrypted).decode()  # return encoded encrypted string

    except Exception as e:
        logger.info("ERROR: Encryption failed.")
        raise HTTPException(status_code=500, detail={"error": str(e)})
