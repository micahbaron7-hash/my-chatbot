
from flask import Flask, request, session, redirect, url_for, render_template_string
from openai import OpenAI
import os
import time
import random
import hmac

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "studyspace-secret-key")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

CODE_CHANGE_HOURS = 3
ADMIN_CODE = "673246"

STARTUP_TIME = time.time()
CURRENT_CODE = str(random.randint(100000, 999999))


def get_code_period():
    elapsed = time.time() - STARTUP_TIME
    return int(elapsed // (CODE_CHANGE_HOURS * 3600))


def get_current_code():
    period = get_code_period()

    random.seed(int(STARTUP_TIME) + period)

    return str(random.randint(100000, 999999))


def check_session():
    return (
        session.get("logged_in")
        and session.get("code_period") == get_code_period()
    )


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
        <h1>S<a href="/ai">t</a>udySpace</h1>
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
            max-width: 800px;
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
        }

        .error {
            color: #dc2626;
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
                    Enter the current access code to continue.
                </p>

                <form method="POST" action="/login">

                    <input
                        type="text"
                        name="code"
                        placeholder="Enter code"
                        autocomplete="off"
                        required
                    >

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

                <h1>Admin</h1>

                <p class="admin-info">
                    Current access code:
                </p>

                <div class="code">
                    {{ current_code }}
                </div>

                <p class="admin-info">
                    This code automatically changes every
                    {{ change_hours }} hours.
                </p>

                <form method="POST" action="/logout">

                    <button type="submit">
                        Log Out
                    </button>

                </form>

            </div>

        {% elif page == "chat" %}

            <div class="chat-box">

                <h1>Study Help</h1>

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


@app.route("/ai")
def ai():

    if check_session():

        if session.get("admin"):

            return render_template_string(
                AI_HTML,
                page="admin",
                current_code=get_current_code(),
                change_hours=CODE_CHANGE_HOURS
            )

        return render_template_string(
            AI_HTML,
            page="chat",
            messages=session.get("messages", [])
        )

    session.clear()

    return render_template_string(
        AI_HTML,
        page="login",
        error=None
    )


@app.route("/login", methods=["POST"])
def login():

    code = request.form.get("code", "").strip()

    if hmac.compare_digest(code, ADMIN_CODE):

        session["logged_in"] = True
        session["admin"] = True
        session["code_period"] = get_code_period()

        return redirect(url_for("ai"))

    current_code = get_current_code()

    if hmac.compare_digest(code, current_code):

        session["logged_in"] = True
        session["admin"] = False
        session["code_period"] = get_code_period()

        session["messages"] = [
            {
                "role": "developer",
                "content": "You are a helpful study assistant. Help the user understand school subjects, explain concepts clearly, and help with studying."
            }
        ]

        return redirect(url_for("ai"))

    return render_template_string(
        AI_HTML,
        page="login",
        error="Incorrect or expired code."
    )


@app.route("/chat", methods=["POST"])
def chat():

    if not check_session() or session.get("admin"):

        session.clear()

        return redirect(url_for("ai"))

    user_message = request.form.get("message", "").strip()

    if not user_message:

        return redirect(url_for("ai"))

    messages = session.get("messages", [])

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    response = client.responses.create(
        model="gpt-5.6",
        input=messages
    )

    answer = response.output_text

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    session["messages"] = messages

    return redirect(url_for("ai"))


@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

