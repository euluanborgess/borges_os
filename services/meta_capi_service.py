import hashlib
import time
import requests
import json
import logging

logger = logging.getLogger(__name__)

def hash_data(data: str) -> str:
    """Hashes a string using SHA256 as required by Meta CAPI."""
    if not data:
        return ""
    return hashlib.sha256(data.strip().lower().encode('utf-8')).hexdigest()

def send_purchase_event(lead_data: dict, value: float, meta_pixel_id: str, meta_capi_token: str, currency: str = "BRL"):
    """
    Sends a 'Purchase' event to Meta Conversion API (CAPI).
    
    lead_data should dict containing:
      - phone: str (e.g., '5511999999999')
      - email: str (optional)
      - name: str (optional)
    """
    if not meta_pixel_id or not meta_capi_token:
        logger.warning("Meta Pixel ID or CAPI Token missing. Skipping CAPI purchase event.")
        return False

    url = f"https://graph.facebook.com/v19.0/{meta_pixel_id}/events"
    
    user_data = {}
    
    # Hash Phone
    if lead_data.get("phone"):
        phone = lead_data["phone"]
        # Ensure it has country code if it doesn't, assuming 55 for Brazil for simplicity if len == 11
        phone_str = str(phone).replace("+", "").replace("-", "").replace(" ", "")
        user_data["ph"] = [hash_data(phone_str)]
        
    # Hash Email
    if lead_data.get("email"):
        user_data["em"] = [hash_data(lead_data["email"])]

    # Generate a unique event ID to avoid duplication
    event_id = f"purchase_{lead_data.get('id', int(time.time()))}_{int(time.time())}"

    payload = {
        "data": [
            {
                "event_name": "Purchase",
                "event_time": int(time.time()),
                "action_source": "system_generated",
                "event_id": event_id,
                "user_data": user_data,
                "custom_data": {
                    "currency": currency,
                    "value": float(value)
                }
            }
        ],
        "access_token": meta_capi_token
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully sent Purchase event to Meta CAPI for event_id: {event_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send event to Meta CAPI: {e}")
        if e.response is not None:
             logger.error(f"Response: {e.response.text}")
        return False
