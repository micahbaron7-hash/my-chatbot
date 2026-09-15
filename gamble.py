from flask import Blueprint, session, redirect, url_for, render_template_string


gamble_bp = Blueprint("gamble", __name__)


GAMBLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Gamble - StudySpace</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            color: #111827;
        }

        header {
            background: white;
            padding: 20px 30px;
            border-bottom: 1px solid #e5e7eb;
        }

        header h1 {
            margin: 0;
            font-size: 28px;
        }

        .container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
        }

        .back {
            display: inline-block;
            margin-bottom: 25px;
            color: #2563eb;
            text-decoration: none;
            font-weight: bold;
        }

        .game-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }

        .game-card h2 {
            margin-top: 0;
        }

        .coming-soon {
            color: #6b7280;
            font-size: 18px;
        }

        .account-name {
            color: #6b7280;
            margin-bottom: 25px;
        }
    </style>
</head>
<body>
    <header>
        <h1>StudySpace</h1>
    </header>

    <div class="container">
        <a href="/study" class="back">← Back to AI</a>

        <div class="game-card">
            <h2>Gamble</h2>
            <div class="account-name">{{ account_name }}</div>
            <p class="coming-soon">Games coming soon.</p>
        </div>
    </div>
</body>
</html>
"""


@gamble_bp.route("/gamble")
def gamble():
    if not session.get("logged_in"):
        return redirect(url_for("study"))

    if session.get("admin"):
        return redirect(url_for("study"))

    return render_template_string(
        GAMBLE_HTML,
        account_name=session.get("account_name", "")
    )
