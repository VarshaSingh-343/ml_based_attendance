# message_store.py
latest_message = {"text": "", "type": "info"}
last_updated = None

def update_message(text, msg_type="info"):
    global latest_message, last_updated
    latest_message = {"text": text, "type": msg_type}
    
    from datetime import datetime
    last_updated = datetime.utcnow().isoformat()
