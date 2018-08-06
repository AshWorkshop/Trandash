import base64
import hashlib
import hmac
import json
import time
from .bitfinex_key import ApiKey, SecretKey


def getHeaders(url, URL, auth=True, payload_params=None):

    if auth:
        payload_object = {
            "request": URL,
            "nonce": str(time.time() * 1000000)  # update nonce each POST request
        }
        if payload_params is not None:
            payload_object.update(payload_params)
        payload = base64.b64encode(bytes(json.dumps(payload_object), "utf-8"))
        signature = hmac.new(SecretKey, msg=payload, digestmod=hashlib.sha384).hexdigest()
        headers = {
            'User-Agent': ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'],
            'Content-Type': ["application/json"],
            'Accept': ["application/json"]
            'X-BFX-APIKEY': [ApiKey],
            'X-BFX-PAYLOAD': [payload],
            'X-BFX-SIGNATURE': [signature]
        }
	return headers