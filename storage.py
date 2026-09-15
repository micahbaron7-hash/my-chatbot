import os
import json
import io
import copy
import threading
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

DRIVE_FILE_ID = os.environ.get("GOOGLE_DRIVE_FILE_ID")
SERVICE = None
LOCK = threading.RLock()

def get_drive_service():
    global SERVICE
    with LOCK:
        if SERVICE is None:
            raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
            if not raw:
                raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
            if not DRIVE_FILE_ID:
                raise RuntimeError("GOOGLE_DRIVE_FILE_ID is not set")
            credentials_info = json.loads(raw)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            SERVICE = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return SERVICE

def _download_accounts():
    service = get_drive_service()
    request_media = service.files().get_media(fileId=DRIVE_FILE_ID)
    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request_media)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    file_data.seek(0)
    raw = file_data.read().decode("utf-8")
    accounts = json.loads(raw) if raw.strip() else {}
    accounts.setdefault("accounts", {})
    accounts.setdefault("refill_codes", {})
    accounts.setdefault("token_requests", {})
    return accounts

def load_accounts(force=True):
    with LOCK:
        return copy.deepcopy(_download_accounts())

def _write_accounts(accounts):
    service = get_drive_service()
    data = json.dumps(accounts, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/json", resumable=False)
    service.files().update(fileId=DRIVE_FILE_ID, media_body=media).execute()

def save_accounts(accounts):
    snapshot = copy.deepcopy(accounts)
    with LOCK:
        _write_accounts(snapshot)
    return True

def save_accounts_async(accounts):
    # Kept for compatibility. Persistence is deliberately synchronous so data cannot be lost.
    return save_accounts(accounts)

def change_account_credits(account_name, amount):
    with LOCK:
        accounts_data = _download_accounts()
        account = accounts_data.get("accounts", {}).get(account_name)
        if not account:
            return None

        used = int(account.get("characters_used", 0))
        maximum = int(account.get("characters_max", 0))

        if amount < 0:
            cost = -int(amount)
            if maximum - used < cost:
                return None
            account["characters_used"] = used + cost
        else:
            account["characters_used"] = used - int(amount)

        _write_accounts(accounts_data)
        return max(0, maximum - int(account.get("characters_used", 0)))
