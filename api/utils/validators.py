from datetime import datetime

def validate_iso_timestamp(timestamp_str: str) -> bool:
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False
