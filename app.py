from flask import Flask, request, session, redirect, url_for, render_template_string
from openai import OpenAI
import os

app = Flask(__name__)
app.secret_key = "change-this-later"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

CODE = "1234"
MAX_LEN = 1000

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>My ChatGPT</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }

        .chat {
            border: 1px solid #ccc;
            padding: 20px;
            min-height: 400px;
            margin-bottom: 15px;
            overflow-y: auto;
        }

        .user {
            margin: 15px 0;
        }

        .assistant {
            margin: 15px 0;
        }

        textarea {
            width: 100%;
            height: 80px;
            box-sizing: border-box;
        }

        button {
            padding: 10px 20px;
            margin-top: 10px;
            cursor: pointer;
        }

        input {
            padding: 10px;
            width: 200px;
        }

        .error {
            color: red;
        }
    </style>
</head>
<body>

{% if not session.get("logged_in") %}

    <h1>My ChatGPT</h1>

    <form method="POST" action="/login">
        <input type="text" name="code" placeholder="Enter code">
        <button type="submit">Enter</button>
    </form>

    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}

{% else %}

    <h1>My ChatGPT</h1>

    <div class="chat">
        {% for message in messages %}
            {% if message.role == "user" %}
                <div class="user">
                    <strong>You:</strong> {{ message.content }}
                </div>
            {% elif message.role == "assistant" %}
                <div class="assistant">
                    <strong>ChatGPT:</strong> {{ message.content }}
                </div>
            {% endif %}
        {% endfor %}
    </div>

    <form method="POST" action="/chat">
        <textarea name="message" placeholder="Type your message..." required></textarea>
        <button type="submit">Send</button>
    </form>

    <p>Remaining output: {{ remaining }}</p>
    <p>Total output: {{ total }}</p>

    <form method="POST" action="/logout">
        <button type="submit">Quit</button>
    </form>

{% endif %}

</body>
</html>
"""

@app.route("/")
def home():
    messages = session.get("messages", [])
    return render_template_string(
        HTML,
        messages=messages,
        remaining=session.get("remaining", MAX_LEN),
        total=session.get("total", 0),
        error=None
    )

@app.route("/login", methods=["POST"])
def login():
    code = request.form.get("code")

    if code == CODE:
        session["logged_in"] = True
        session["messages"] = [
            {
                "role": "developer",
                "content": "You are ChatGPT."
            }
        ]
        session["remaining"] = MAX_LEN
        session["total"] = 0
        return redirect(url_for("home"))

    return render_template_string(
        HTML,
        messages=[],
        remaining=MAX_LEN,
        total=0,
        error="Incorrect code."
    )

@app.route("/chat", methods=["POST"])
def chat():
    if not session.get("logged_in"):
        return redirect(url_for("home"))

    user_message = request.form.get("message")

    if not user_message:
        return redirect(url_for("home"))

    messages = session.get("messages", [])

    messages.append({
        "role": "user",
        "content": user_message
    })

    response = client.responses.create(
        model="gpt-5.6",
        input=messages
    )

    answer = response.output_text
    length = len(answer)

    remaining = session.get("remaining", MAX_LEN)
    total = session.get("total", 0)

    total += length
    remaining -= length

    if remaining < 0:
        remaining = 0

    messages.append({
        "role": "assistant",
        "content": answer
    })

    session["messages"] = messages
    session["remaining"] = remaining
    session["total"] = total

    return redirect(url_for("home"))

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)