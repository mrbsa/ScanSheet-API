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
        decoded_payload = base64.b64decode(encrypted_payload)
        nonce = decoded_payload[:12]  # 12-byte nonce
        ciphertext = decoded_payload[12:-16]
        tag = decoded_payload[-16:]

        decryption_key = base64.b64decode(decryption_key_b64)
        aesgcm = AESGCM(decryption_key)
        decrypted = aesgcm.decrypt(nonce, ciphertext + tag, None)

        return json.loads(decrypted)
    
    except Exception as e:
        logger.info("ERROR: Cryptography failed.")
        raise HTTPException(status_code=500, detail={"error": str(e)})
