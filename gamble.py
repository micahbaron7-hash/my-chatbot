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
            background: #f4f7fb;
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
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
        }

        .header {
            background: white;
            border-radius: 18px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
            margin-bottom: 25px;
        }

        .header h1 {
            margin-top: 0;
        }

        .header p {
            color: #6b7280;
        }

        .games {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 18px;
        }

        .game {
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
            text-align: center;
        }

        .game-icon {
            font-size: 45px;
            margin-bottom: 15px;
        }

        .game h2 {
            margin: 0 0 10px;
        }

        .game p {
            color: #6b7280;
        }

        .coming {
            display: inline-block;
            margin-top: 10px;
            padding: 9px 15px;
            background: #e5e7eb;
            color: #6b7280;
            border-radius: 8px;
            font-weight: bold;
        }
    </style>
</head>

<body>

    <div class="top">
        <a href="/study">← Back to AI</a>
    </div>

    <div class="container">

        <div class="header">
            <h1>Gamble</h1>
            <p>Use your StudySpace credits in games.</p>
        </div>

        <div class="games">

            <div class="game">
                <div class="game-icon">🎰</div>
                <h2>Slots</h2>
                <p>Spin the reels and try your luck.</p>
                <span class="coming">Coming Soon</span>
            </div>

            <div class="game">
                <div class="game-icon">🃏</div>
                <h2>Blackjack</h2>
                <p>Play against the dealer.</p>
                <span class="coming">Coming Soon</span>
            </div>

            <div class="game">
                <div class="game-icon">🎡</div>
                <h2>Roulette</h2>
                <p>Pick a number, color, or bet.</p>
                <span class="coming">Coming Soon</span>
            </div>

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

    return render_template_string(GAMBLE_HTML)
