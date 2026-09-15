import os
import json
import io
import copy
import time
import threading
import queue
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

DRIVE_FILE_ID = os.environ.get("GOOGLE_DRIVE_FILE_ID")
CACHE_TTL = 3.0
SERVICE = None
CACHE = None
CACHE_TIME = 0.0
LOCK = threading.RLock()
SAVE_QUEUE = queue.Queue()

def get_drive_service():
    global SERVICE
    with LOCK:
        if SERVICE is None:
            credentials_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
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
    accounts = json.loads(file_data.read().decode("utf-8"))
    accounts.setdefault("accounts", {})
    accounts.setdefault("refill_codes", {})
    accounts.setdefault("token_requests", {})
    return accounts

def load_accounts(force=False):
    global CACHE, CACHE_TIME
    with LOCK:
        now = time.monotonic()
        if not force and CACHE is not None and now - CACHE_TIME < CACHE_TTL:
            return copy.deepcopy(CACHE)
        CACHE = _download_accounts()
        CACHE_TIME = now
        return copy.deepcopy(CACHE)

def _write_accounts(accounts):
    service = get_drive_service()
    data = json.dumps(accounts, separators=(",", ":")).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/json", resumable=False)
    service.files().update(fileId=DRIVE_FILE_ID, media_body=media).execute()

def save_accounts(accounts):
    global CACHE, CACHE_TIME
    snapshot = copy.deepcopy(accounts)
    with LOCK:
        CACHE = snapshot
        CACHE_TIME = time.monotonic()
        _write_accounts(snapshot)

def save_accounts_async(accounts):
    global CACHE, CACHE_TIME
    snapshot = copy.deepcopy(accounts)
    with LOCK:
        CACHE = snapshot
        CACHE_TIME = time.monotonic()
    SAVE_QUEUE.put(snapshot)

def _save_worker():
    while True:
        snapshot = SAVE_QUEUE.get()
        try:
            with LOCK:
                _write_accounts(snapshot)
        except Exception:
            pass
        finally:
            SAVE_QUEUE.task_done()

threading.Thread(target=_save_worker, daemon=True).start()
