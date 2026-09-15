from gamble import gamble_bp
from flask import Flask, request, session, redirect, url_for, render_template_string
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import os
import random
import hmac
import json
import io
import threading
import math

app = Flask(__name__)
app.register_blueprint(gamble_bp)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "studyspace-secret-key")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

ADMIN_CODE = "673246"
ACCOUNT_MAX = 0

DRIVE_FILE_ID = os.environ.get("GOOGLE_DRIVE_FILE_ID")
DRIVE_LOCK = threading.Lock()


def check_session():
    return session.get("logged_in")


def get_drive_service():
    credentials_info = json.loads(
        os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    )

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    return build("drive", "v3", credentials=credentials)


def load_accounts():
    service = get_drive_service()

    request_media = service.files().get_media(
        fileId=DRIVE_FILE_ID
    )

    file_data = io.BytesIO()

    downloader = MediaIoBaseDownload(
        file_data,
        request_media
    )

    done = False

    while not done:
        _, done = downloader.next_chunk()

    file_data.seek(0)

    accounts = json.loads(
        file_data.read().decode("utf-8")
    )

    if "accounts" not in accounts:
        accounts["accounts"] = {}

    if "refill_codes" not in accounts:
        accounts["refill_codes"] = {}

    return accounts


def save_accounts(accounts):
    service = get_drive_service()

    data = json.dumps(
        accounts,
        indent=4
    ).encode("utf-8")

    media = MediaIoBaseUpload(
        io.BytesIO(data),
        mimetype="application/json",
        resumable=False
    )

    service.files().update(
        fileId=DRIVE_FILE_ID,
        media_body=media
    ).execute()


def generate_unique_code(existing_codes):
    while True:
        code = str(random.randint(100000, 999999))

        if code not in existing_codes:
            return code


HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>StudySpace</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #1f2937;
        }

        .header {
            background: white;
            padding: 22px 40px;
            border-bottom: 1px solid #e5e7eb;
        }

        .header h1 {
            margin: 0;
            font-size: 28px;
        }

        .header h1 a {
            color: inherit;
            text-decoration: none;
        }

        .header p {
            margin: 6px 0 0;
            color: #6b7280;
        }

        .container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
        }

        .welcome {
            background: white;
            border-radius: 18px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        }

        .welcome h2 {
            margin-top: 0;
            font-size: 30px;
        }

        .welcome p {
            color: #6b7280;
            font-size: 17px;
        }

        .section-title {
            margin: 25px 0 15px;
            font-size: 21px;
        }

        .tools {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
        }

        .tool {
            background: white;
            border: none;
            border-radius: 16px;
            padding: 24px;
            text-align: left;
            text-decoration: none;
            color: #1f2937;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            transition: 0.2s;
            display: block;
        }

        .tool:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.10);
        }

        .tool-icon {
            font-size: 30px;
            margin-bottom: 12px;
        }

        .tool-title {
            font-size: 18px;
            font-weight: bold;
        }

        .tool-description {
            color: #6b7280;
            margin-top: 7px;
            font-size: 14px;
        }

        .footer {
            text-align: center;
            color: #9ca3af;
            padding: 35px 20px;
            font-size: 13px;
        }
    </style>
</head>

<body>

    <div class="header">
        <h1>S<a href="/study">t</a>udySpace</h1>
        <p>Your place to study and stay organized</p>
    </div>

    <div class="container">

        <div class="welcome">
            <h2>Welcome to StudySpace</h2>
            <p>
                Use the tools below to study, organize your work,
                and get help when you need it.
            </p>
        </div>

        <div class="section-title">
            Study Tools
        </div>

        <div class="tools">

            <a class="tool" href="https://docs.google.com/" target="_blank">
                <div class="tool-icon">📝</div>
                <div class="tool-title">Google Docs</div>
                <div class="tool-description">
                    Write and edit your assignments.
                </div>
            </a>

            <a class="tool" href="https://drive.google.com/" target="_blank">
                <div class="tool-icon">📁</div>
                <div class="tool-title">Google Drive</div>
                <div class="tool-description">
                    Access your saved school files.
                </div>
            </a>

            <a class="tool" href="https://classroom.google.com/" target="_blank">
                <div class="tool-icon">🎓</div>
                <div class="tool-title">Google Classroom</div>
                <div class="tool-description">
                    Check assignments and classwork.
                </div>
            </a>

            <a class="tool" href="https://www.google.com/" target="_blank">
                <div class="tool-icon">🔎</div>
                <div class="tool-title">Search</div>
                <div class="tool-description">
                    Search the web for information.
                </div>
            </a>

            <a class="tool" href="https://open.spotify.com/" target="_blank">
                <div class="tool-icon">🎵</div>
                <div class="tool-title">Spotify</div>
                <div class="tool-description">
                    Listen to music while you study.
                </div>
            </a>

            <a class="tool" href="https://www.google.com/search?q=calculator" target="_blank">
                <div class="tool-icon">🧮</div>
                <div class="tool-title">Calculator</div>
                <div class="tool-description">
                    Solve calculations and math problems.
                </div>
            </a>

            <a class="tool" href="https://canvas.instructure.com/" target="_blank">
                <div class="tool-icon">📚</div>
                <div class="tool-title">Canvas</div>
                <div class="tool-description">
                    Access your courses and assignments.
                </div>
            </a>

            <a class="tool" href="https://www.canva.com/" target="_blank">
                <div class="tool-icon">🎨</div>
                <div class="tool-title">Canva</div>
                <div class="tool-description">
                    Create presentations and designs.
                </div>
            </a>

            <a class="tool" href="https://www.desmos.com/calculator" target="_blank">
                <div class="tool-icon">📊</div>
                <div class="tool-title">Desmos</div>
                <div class="tool-description">
                    Graph equations and explore math.
                </div>
            </a>

            <a class="tool" href="https://www.kahoot.com" target="_blank">
                <div class="tool-icon">🎮</div>
                <div class="tool-title">Kahoot</div>
                <div class="tool-description">
                    Join quizzes and test your knowledge.
                </div>
            </a>

            <a class="tool" href="https://mail.google.com/" target="_blank">
                <div class="tool-icon">📨</div>
                <div class="tool-title">Gmail</div>
                <div class="tool-description">
                    Send and manage your emails.
                </div>
            </a>

            <a class="tool" href="https://vclock.com/timer/" target="_blank">
                <div class="tool-icon">⏱️</div>
                <div class="tool-title">Timer</div>
                <div class="tool-description">
                    Set a timer for studying, homework, or breaks.
                </div>
            </a>

        </div>
    </div>

    <div class="footer">
        StudySpace
    </div>

</body>
</html>
"""


AI_HTML = """
<!DOCTYPE html>
<html>

<head>
    <title>StudySpace</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            margin: 0;
            color: #1f2937;
        }

        .top {
            background: white;
            padding: 18px 25px;
            border-bottom: 1px solid #e5e7eb;
        }

        .top a {
            text-decoration: none;
            color: #374151;
            font-weight: bold;
        }

        .container {
            max-width: 900px;
            margin: 30px auto;
            padding: 20px;
        }

        .login,
        .chat-box,
        .admin-box {
            background: white;
            border-radius: 18px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        }

        h1 {
            margin-top: 0;
        }

        .chat {
            min-height: 400px;
            max-height: 550px;
            overflow-y: auto;
            margin-bottom: 20px;
        }

        .user,
        .assistant {
            padding: 14px;
            margin: 12px 0;
            border-radius: 12px;
        }

        .user {
            background: #eef2ff;
        }

        .assistant {
            background: #f3f4f6;
        }

        textarea {
            width: 100%;
            height: 90px;
            resize: vertical;
            padding: 12px;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            font-size: 15px;
        }

        button {
            padding: 11px 22px;
            margin-top: 10px;
            border: none;
            border-radius: 9px;
            background: #1f2937;
            color: white;
            cursor: pointer;
        }

        input {
            padding: 12px;
            width: 220px;
            border: 1px solid #d1d5db;
            border-radius: 9px;
            margin-bottom: 8px;
        }

        .error {
            color: #dc2626;
        }

        .success {
            color: #16a34a;
        }

        .code {
            font-size: 40px;
            font-weight: bold;
            letter-spacing: 5px;
            margin: 25px 0;
            text-align: center;
        }

        .admin-info {
            color: #6b7280;
        }

        .account {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 15px;
            margin: 12px 0;
        }

        .account-code {
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 3px;
        }

        .admin-section {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }

        .warning {
            color: #dc2626;
        }

        .delete-button {
            background: #dc2626;
        }

        .remaining {
            color: #2563eb;
            font-weight: bold;
        }
    </style>
</head>

<body>

    <div class="top">
        <a href="/">← Back to StudySpace</a>
    </div>

    <div class="container">

        {% if page == "login" %}

            <div class="login">

                <h1>Study Help</h1>

                <p>
                    Enter your permanent account code.
                </p>

                <form method="POST" action="/login">

                    <input
                        type="text"
                        name="account_code"
                        placeholder="Permanent account code"
                        autocomplete="off"
                        required
                    >

                    <br>

                    <button type="submit">
                        Enter
                    </button>

                </form>

                {% if error %}
                    <p class="error">
                        {{ error }}
                    </p>
                {% endif %}

            </div>

        {% elif page == "admin" %}

            <div class="admin-box">

                <h1>Admin Panel</h1>

                <p class="admin-info">
                    Permanent account codes are saved and do not expire. Refill codes are global and can only be used once.
                </p>

                <div class="admin-section">

                    <h2>Create Account</h2>

                    <form method="POST" action="/admin/create">

                        <input
                            type="text"
                            name="name"
                            placeholder="Person's name"
                            required
                        >

                        <br>

                        <button type="submit">
                            Create Account
                        </button>

                    </form>

                    {% if created_name %}

                        <p class="success">
                            Account created for {{ created_name }}.
                        </p>

                        <p>
                            Permanent account code:
                        </p>

                        <div class="code">
                            {{ created_code }}
                        </div>

                    {% endif %}

                </div>

                <div class="admin-section">

                    <h2>Accounts</h2>

                    {% if accounts %}

                        {% for account in accounts %}

                            <div class="account">

                                <strong>{{ account.name }}</strong>

                                <p>
                                    Permanent code:
                                    <span class="account-code">
                                        {{ account.code }}
                                    </span>
                                </p>

                                <p>
                                    Characters used:
                                    {{ account.used }}
                                    /
                                    {{ account.maximum }}
                                </p>

                                <p class="remaining">
                                    Remaining:
                                    {{ account.remaining }}
                                </p>

                                <form method="POST" action="/admin/remove">

                                    <input
                                        type="hidden"
                                        name="account_code"
                                        value="{{ account.code }}"
                                    >

                                    <input
                                        type="number"
                                        name="amount"
                                        placeholder="Characters to remove"
                                        min="1"
                                        required
                                    >

                                    <br>

                                    <button type="submit">
                                        Remove Characters
                                    </button>

                                </form>

                                <form method="POST" action="/admin/delete" onsubmit="return confirm('Are you sure you want to permanently delete this account?');">

                                    <input
                                        type="hidden"
                                        name="account_code"
                                        value="{{ account.code }}"
                                    >

                                    <button type="submit" class="delete-button">
                                        Delete Account
                                    </button>

                                </form>

                            </div>

                        {% endfor %}

                    {% else %}

                        <p>
                            No accounts have been created yet.
                        </p>

                    {% endif %}

                </div>

                {% if refill_code %}

                    <div class="admin-section">

                        <h2>New Refill Code</h2>

                        <p>
                            Anyone can use this code once.
                        </p>

                        <div class="code">
                            {{ refill_code }}
                        </div>

                        <p class="warning">
                            This code can only be used once.
                        </p>

                    </div>

                {% endif %}

                <div class="admin-section">

                    <h2>Create Global Refill Code</h2>

                    <p>
                        Choose how many characters the code gives. Anyone can use it once.
                    </p>

                    <form method="POST" action="/admin/refill">

                        <input
                            type="number"
                            name="amount"
                            placeholder="Characters to add"
                            min="1"
                            required
                        >

                        <br>

                        <button type="submit">
                            Generate Refill Code
                        </button>

                    </form>

                </div>

                <form method="POST" action="/logout">

                    <button type="submit">
                        Log Out
                    </button>

                </form>

            </div>

        {% elif page == "chat" %}

            <div class="chat-box">

                <h1>Study Help</h1>

                <p>
                    Account: <strong>{{ account_name }}</strong>
                </p>

                <p class="remaining">
                    Characters remaining:
                    {{ remaining }}
                </p>

                <div class="chat">

                    {% for message in messages %}

                        {% if message.role == "user" %}

                            <div class="user">
                                <strong>You:</strong><br>
                                {{ message.content }}
                            </div>

                        {% elif message.role == "assistant" %}

                            <div class="assistant">
                                <strong>Study Help:</strong><br>
                                {{ message.content }}
                            </div>

                        {% endif %}

                    {% endfor %}

                </div>

                {% if remaining > 0 %}

                    <form method="POST" action="/chat">

                        <textarea
                            name="message"
                            placeholder="What are you working on?"
                            required
                        ></textarea>

                        <button type="submit">
                            Send
                        </button>

                    </form>

                {% else %}

                    <p class="error">
                        Your account has used all of its available characters.
                    </p>

                {% endif %}

                <div class="admin-section">

                    <h2>Have a refill code?</h2>

                    <form method="POST" action="/redeem">

                        <input
                            type="text"
                            name="refill_code"
                            placeholder="Enter refill code"
                            autocomplete="off"
                            required
                        >

                        <button type="submit">
                            Redeem
                        </button>

                    </form>

                    {% if redeem_message %}

                        <p class="{{ redeem_class }}">
                            {{ redeem_message }}
                        </p>

                    {% endif %}

                </div>
                
                <a href="/gamble" style="text-decoration:none;">
                    <button type="button">
                        Gamble
                    </button>
                 </a>

                <form method="POST" action="/logout">

                    <button type="submit">
                        Log Out
                    </button>

                </form>

            </div>

        {% endif %}

    </div>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HOME_HTML)


@app.route("/study")
def study():

    if session.get("admin"):

        accounts_data = load_accounts()

        account_list = []

        for name, account in accounts_data["accounts"].items():

            used = account.get("characters_used", 0)
            maximum = account.get("characters_max", ACCOUNT_MAX)

            account_list.append(
                {
                    "name": name,
                    "code": account["account_code"],
                    "used": used,
                    "maximum": maximum,
                    "remaining": max(0, maximum - used)
                }
            )

        return render_template_string(
            AI_HTML,
            page="admin",
            accounts=account_list,
            created_name=None,
            created_code=None,
            refill_code=None
        )

    if check_session():

        accounts = load_accounts()

        account_name = session.get("account_name")

        if account_name not in accounts["accounts"]:

            session.clear()

            return redirect(url_for("study"))

        account = accounts["accounts"][account_name]

        used = account.get("characters_used", 0)
        maximum = account.get("characters_max", ACCOUNT_MAX)

        return render_template_string(
            AI_HTML,
            page="chat",
            messages=session.get("messages", []),
            account_name=account_name,
            remaining=max(0, maximum - used),
            redeem_message=None,
            redeem_class=""
        )

    session.clear()

    return render_template_string(
        AI_HTML,
        page="login",
        error=None
    )


@app.route("/login", methods=["POST"])
def login():

    account_code = request.form.get("account_code", "").strip()

    if hmac.compare_digest(account_code, ADMIN_CODE):

        session["logged_in"] = True
        session["admin"] = True

        return redirect(url_for("study"))

    accounts_data = load_accounts()

    found_account = None

    for name, account in accounts_data["accounts"].items():

        if hmac.compare_digest(
            account.get("account_code", ""),
            account_code
        ):

            found_account = name
            break

    if found_account is None:

        return render_template_string(
            AI_HTML,
            page="login",
            error="Incorrect account code."
        )

    session["logged_in"] = True
    session["admin"] = False
    session["account_name"] = found_account

    session["messages"] = [
        {
            "role": "developer",
            "content": "You are a helpful study assistant. Help the user understand school subjects, explain concepts clearly, and help with studying."
        }
    ]

    return redirect(url_for("study"))


@app.route("/admin/create", methods=["POST"])
def create_account():

    if not session.get("admin"):

        session.clear()

        return redirect(url_for("study"))

    name = request.form.get("name", "").strip()

    if not name:

        return redirect(url_for("study"))

    with DRIVE_LOCK:

        accounts_data = load_accounts()

        if name in accounts_data["accounts"]:

            account_list = []

            for account_name, account in accounts_data["accounts"].items():

                used = account.get("characters_used", 0)
                maximum = account.get("characters_max", ACCOUNT_MAX)

                account_list.append(
                    {
                        "name": account_name,
                        "code": account["account_code"],
                        "used": used,
                        "maximum": maximum,
                        "remaining": max(0, maximum - used)
                    }
                )

            return render_template_string(
                AI_HTML,
                page="admin",
                accounts=account_list,
                created_name=None,
                created_code=None,
                refill_code=None
            )

        existing_codes = {
            account.get("account_code")
            for account in accounts_data["accounts"].values()
        }

        account_code = generate_unique_code(existing_codes)

        accounts_data["accounts"][name] = {
            "account_code": account_code,
            "characters_used": 0,
            "characters_max": ACCOUNT_MAX
        }

        save_accounts(accounts_data)

    account_list = []

    for account_name, account in accounts_data["accounts"].items():

        used = account.get("characters_used", 0)
        maximum = account.get("characters_max", ACCOUNT_MAX)

        account_list.append(
            {
                "name": account_name,
                "code": account["account_code"],
                "used": used,
                "maximum": maximum,
                "remaining": max(0, maximum - used)
            }
        )

    return render_template_string(
        AI_HTML,
        page="admin",
        accounts=account_list,
        created_name=name,
        created_code=account_code,
        refill_code=None
    )


@app.route("/admin/refill", methods=["POST"])
def create_refill():

    if not session.get("admin"):
        session.clear()
        return redirect(url_for("study"))

    try:
        amount = int(request.form.get("amount", "0"))
    except:
        amount = 0

    if amount <= 0:
        return redirect(url_for("study"))

    with DRIVE_LOCK:
        accounts_data = load_accounts()

        existing_refill_codes = set(
            accounts_data.get("refill_codes", {}).keys()
        )

        refill_code = generate_unique_code(existing_refill_codes)

        accounts_data["refill_codes"][refill_code] = {
            "amount": amount
        }

        save_accounts(accounts_data)

    account_list = []

    for account_name, account in accounts_data["accounts"].items():

        used = account.get("characters_used", 0)
        maximum = account.get("characters_max", ACCOUNT_MAX)

        account_list.append(
            {
                "name": account_name,
                "code": account["account_code"],
                "used": used,
                "maximum": maximum,
                "remaining": max(0, maximum - used)
            }
        )

    return render_template_string(
        AI_HTML,
        page="admin",
        accounts=account_list,
        created_name=None,
        created_code=None,
        refill_code=refill_code
    )


@app.route("/admin/remove", methods=["POST"])
def remove_characters():

    if not session.get("admin"):
        session.clear()
        return redirect(url_for("study"))

    account_code = request.form.get("account_code", "").strip()

    try:
        amount = int(request.form.get("amount", "0"))
    except:
        amount = 0

    if amount <= 0:
        return redirect(url_for("study"))

    with DRIVE_LOCK:
        accounts_data = load_accounts()

        found_account = None

        for account_name, account in accounts_data["accounts"].items():
            if hmac.compare_digest(
                account.get("account_code", ""),
                account_code
            ):
                found_account = account_name
                break

        if found_account is None:
            return redirect(url_for("study"))

        account = accounts_data["accounts"][found_account]

        maximum = account.get("characters_max", ACCOUNT_MAX)
        used = account.get("characters_used", 0)

        remaining = max(0, maximum - used)
        remove_amount = min(amount, remaining)

        account["characters_max"] = maximum - remove_amount

        save_accounts(accounts_data)

    account_list = []

    for account_name, account in accounts_data["accounts"].items():

        used = account.get("characters_used", 0)
        maximum = account.get("characters_max", ACCOUNT_MAX)

        account_list.append(
            {
                "name": account_name,
                "code": account["account_code"],
                "used": used,
                "maximum": maximum,
                "remaining": max(0, maximum - used)
            }
        )

    return render_template_string(
        AI_HTML,
        page="admin",
        accounts=account_list,
        created_name=None,
        created_code=None,
        refill_code=None
    )


@app.route("/admin/delete", methods=["POST"])
def delete_account():

    if not session.get("admin"):
        session.clear()
        return redirect(url_for("study"))

    account_code = request.form.get("account_code", "").strip()

    with DRIVE_LOCK:
        accounts_data = load_accounts()
        found_account = None

        for account_name, account in accounts_data["accounts"].items():
            if hmac.compare_digest(
                str(account.get("account_code", "")),
                account_code
            ):
                found_account = account_name
                break

        if found_account is None:
            return redirect(url_for("study"))

        del accounts_data["accounts"][found_account]
        save_accounts(accounts_data)

    account_list = []

    for account_name, account in accounts_data["accounts"].items():
        used = account.get("characters_used", 0)
        maximum = account.get("characters_max", ACCOUNT_MAX)

        account_list.append(
            {
                "name": account_name,
                "code": account["account_code"],
                "used": used,
                "maximum": maximum,
                "remaining": max(0, maximum - used)
            }
        )

    return render_template_string(
        AI_HTML,
        page="admin",
        accounts=account_list,
        created_name=None,
        created_code=None,
        refill_code=None
    )


@app.route("/redeem", methods=["POST"])
def redeem():

    if not check_session() or session.get("admin"):
        session.clear()
        return redirect(url_for("study"))

    refill_code = request.form.get("refill_code", "").strip()
    account_name = session.get("account_name")

    with DRIVE_LOCK:
        accounts_data = load_accounts()

        if refill_code not in accounts_data["refill_codes"]:
            account = accounts_data["accounts"].get(account_name)

            used = account.get("characters_used", 0)
            maximum = account.get("characters_max", ACCOUNT_MAX)

            return render_template_string(
                AI_HTML,
                page="chat",
                messages=session.get("messages", []),
                account_name=account_name,
                remaining=max(0, maximum - used),
                redeem_message="Invalid or already-used refill code.",
                redeem_class="error"
            )

        refill = accounts_data["refill_codes"][refill_code]
        amount = refill["amount"]

        accounts_data["accounts"][account_name]["characters_max"] = (
            accounts_data["accounts"][account_name].get(
                "characters_max",
                ACCOUNT_MAX
            ) + amount
        )

        del accounts_data["refill_codes"][refill_code]

        save_accounts(accounts_data)

    account = accounts_data["accounts"][account_name]

    used = account.get("characters_used", 0)
    maximum = account.get("characters_max", ACCOUNT_MAX)

    return render_template_string(
        AI_HTML,
        page="chat",
        messages=session.get("messages", []),
        account_name=account_name,
        remaining=max(0, maximum - used),
        redeem_message=f"{amount:,} characters were added to your account.",
        redeem_class="success"
    )


@app.route("/chat", methods=["POST"])
def chat():

    if not check_session() or session.get("admin"):
        session.clear()
        return redirect(url_for("study"))

    user_message = request.form.get("message", "").strip()

    if not user_message:
        return redirect(url_for("study"))

    account_name = session.get("account_name")

    with DRIVE_LOCK:
        accounts_data = load_accounts()

        if account_name not in accounts_data["accounts"]:
            session.clear()
            return redirect(url_for("study"))

        account = accounts_data["accounts"][account_name]

        used = account.get("characters_used", 0)
        maximum = account.get("characters_max", ACCOUNT_MAX)

        messages = session.get("messages", [])

        input_characters = len(user_message)
        remaining = max(0, maximum - used)

        if input_characters > remaining:
            return render_template_string(
                AI_HTML,
                page="chat",
                messages=messages,
                account_name=account_name,
                remaining=remaining,
                redeem_message="Your message is longer than your remaining characters.",
                redeem_class="error"
            )

        response_characters_available = remaining - input_characters

        if response_characters_available <= 0:
            return render_template_string(
                AI_HTML,
                page="chat",
                messages=messages,
                account_name=account_name,
                remaining=remaining,
                redeem_message="You do not have enough characters left for a response.",
                redeem_class="error"
            )

        if response_characters_available < 16:
            return render_template_string(
                AI_HTML,
                page="chat",
                messages=messages,
                account_name=account_name,
                remaining=remaining,
                redeem_message="You do not have enough characters left for a response.",
                redeem_class="error"
            )

        response_token_limit = max(
            16,
            math.ceil(response_characters_available / 4)
        )

        try:
            response = client.responses.create(
                model="gpt-5.6",
                input=messages + [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                max_output_tokens=response_token_limit
            )

            answer = response.output_text

        except Exception as e:
            return render_template_string(
                AI_HTML,
                page="chat",
                messages=messages,
                account_name=account_name,
                remaining=remaining,
                redeem_message=f"Error: {str(e)}",
                redeem_class="error"
            )

        response_characters = len(answer)
        total_characters = input_characters + response_characters

        if total_characters > remaining:
            answer = answer[:max(0, remaining - input_characters)]
            response_characters = len(answer)
            total_characters = input_characters + response_characters

        messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        account["characters_used"] = used + total_characters

        save_accounts(accounts_data)

    session["messages"] = messages

    return redirect(url_for("study"))


@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
