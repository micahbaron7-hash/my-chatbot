from flask import Blueprint, session, redirect, url_for, render_template_string, request
import random

gamble_bp = Blueprint("gamble", __name__)

GAMBLE_CODE = "2468"

GAMBLE_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Casino - StudySpace</title>
    <style>
        * { box-sizing: border-box; }
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
            max-width: 500px;
            margin: 80px auto;
            padding: 20px;
        }
        .box {
            background: white;
            border-radius: 18px;
            padding: 35px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06);
            text-align: center;
        }
        h1 { margin-top: 0; }
        p { color: #6b7280; }
        input {
            width: 100%;
            padding: 13px;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            margin: 15px 0;
            font-size: 16px;
            text-align: center;
        }
        button {
            width: 100%;
            padding: 13px;
            border: none;
            border-radius: 10px;
            background: #2563eb;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background: #1d4ed8;
        }
        .error {
            color: #dc2626;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="top">
    <a href="/study">← Back to AI</a>
</div>

<div class="container">
    <div class="box">
        <h1>Casino</h1>
        <p>Enter the casino access code.</p>

        <form method="POST" action="/gamble/unlock">
            <input
                type="password"
                name="gamble_code"
                placeholder="Casino code"
                autocomplete="off"
                required
            >

            <button type="submit">
                Enter Casino
            </button>
        </form>

        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</div>

</body>
</html>
"""

GAMBLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Casino - StudySpace</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
        }

        .top {
            background: #1f2937;
            padding: 18px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #374151;
        }

        .top a {
            text-decoration: none;
            color: white;
            font-weight: bold;
        }

        .logout {
            background: #dc2626;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
        }

        .container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
        }

        .header {
            background: #1f2937;
            border-radius: 18px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
        }

        .header h1 {
            margin: 0 0 10px;
            font-size: 36px;
        }

        .balance {
            font-size: 20px;
            font-weight: bold;
            color: #fbbf24;
        }

        .games {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 18px;
        }

        .game {
            background: #1f2937;
            border-radius: 16px;
            padding: 25px;
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
            color: #9ca3af;
        }

        .play {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 16px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }

        .coming {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 16px;
            background: #374151;
            color: #9ca3af;
            border-radius: 8px;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="top">
    <a href="/study">← Back to AI</a>

    <form method="POST" action="/gamble/logout">
        <button class="logout" type="submit">
            Log Out
        </button>
    </form>
</div>

<div class="container">

    <div class="header">
        <h1>🎰 Casino</h1>
        <p>Welcome to the StudySpace casino.</p>

        <div class="balance">
            Demo Credits: {{ balance }}
        </div>
    </div>

    <div class="games">

        <div class="game">
            <div class="game-icon">🃏</div>

            <h2>Blackjack</h2>

            <p>
                Try to get closer to 21 than the dealer.
            </p>

            <a class="play" href="/gamble/blackjack">
                Play Blackjack
            </a>
        </div>

        <div class="game">
            <div class="game-icon">🎰</div>

            <h2>Slots</h2>

            <p>
                Spin the reels and try your luck.
            </p>

            <span class="coming">
                Coming Soon
            </span>
        </div>

        <div class="game">
            <div class="game-icon">🎡</div>

            <h2>Roulette</h2>

            <p>
                Pick a number, color, or bet.
            </p>

            <span class="coming">
                Coming Soon
            </span>
        </div>

    </div>

</div>

</body>
</html>
"""

BLACKJACK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Blackjack - StudySpace</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #064e3b;
            color: white;
        }

        .top {
            background: #022c22;
            padding: 18px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .top a {
            color: white;
            text-decoration: none;
            font-weight: bold;
        }

        .logout {
            background: #dc2626;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
        }

        .container {
            max-width: 900px;
            margin: 35px auto;
            padding: 20px;
        }

        .table {
            background: #047857;
            border-radius: 20px;
            padding: 30px;
            min-height: 500px;
            text-align: center;
        }

        .balance {
            font-size: 20px;
            color: #fbbf24;
            font-weight: bold;
        }

        .section {
            margin: 30px 0;
        }

        .cards {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin: 15px 0;
        }

        .card {
            width: 75px;
            height: 105px;
            background: white;
            color: black;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: bold;
        }

        .bet {
            margin: 25px 0;
        }

        .bet input {
            padding: 12px;
            width: 160px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }

        button {
            padding: 12px 18px;
            border: none;
            border-radius: 8px;
            background: #fbbf24;
            color: #111827;
            font-weight: bold;
            cursor: pointer;
            margin: 5px;
        }

        .message {
            font-size: 22px;
            font-weight: bold;
            margin: 25px 0;
        }

        .error {
            color: #fecaca;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="top">
    <a href="/gamble">← Back to Casino</a>

    <form method="POST" action="/gamble/logout">
        <button class="logout" type="submit">
            Log Out
        </button>
    </form>
</div>

<div class="container">

    <div class="table">

        <h1>🃏 Blackjack</h1>

        <div class="balance">
            Demo Credits: {{ balance }}
        </div>

        {% if not game_started %}

            <div class="bet">

                <form method="POST" action="/gamble/blackjack/start">

                    <p>How many credits do you want to bet?</p>

                    <input
                        type="number"
                        name="bet"
                        min="1"
                        max="{{ balance }}"
                        required
                    >

                    <br>

                    <button type="submit">
                        Deal
                    </button>

                </form>

            </div>

            {% if message %}
                <div class="message">
                    {{ message }}
                </div>
            {% endif %}

        {% else %}

            <div class="section">
                <h2>Dealer</h2>

                <div class="cards">
                    {% for card in dealer_cards %}
                        <div class="card">
                            {{ card }}
                        </div>
                    {% endfor %}
                </div>

                {% if dealer_total is not none %}
                    <p>Total: {{ dealer_total }}</p>
                {% endif %}
            </div>

            <div class="section">
                <h2>You</h2>

                <div class="cards">
                    {% for card in player_cards %}
                        <div class="card">
                            {{ card }}
                        </div>
                    {% endfor %}
                </div>

                <p>Total: {{ player_total }}</p>
            </div>

            <p>Bet: {{ bet }}</p>

            {% if message %}
                <div class="message">
                    {{ message }}
                </div>
            {% endif %}

            {% if active %}

                <form method="POST" action="/gamble/blackjack/hit">
                    <button type="submit">
                        Hit
                    </button>
                </form>

                <form method="POST" action="/gamble/blackjack/stand">
                    <button type="submit">
                        Stand
                    </button>
                </form>

            {% else %}

                <a href="/gamble/blackjack">
                    <button type="button">
                        Play Again
                    </button>
                </a>

            {% endif %}

        {% endif %}

    </div>

</div>

</body>
</html>
"""


def check_gamble_access():
    return (
        session.get("logged_in")
        and not session.get("admin")
        and session.get("gamble_unlocked")
    )


def create_deck():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = [
        "2", "3", "4", "5", "6", "7", "8", "9",
        "10", "J", "Q", "K", "A"
    ]

    deck = []

    for suit in suits:
        for rank in ranks:
            deck.append(rank + suit)

    random.shuffle(deck)

    return deck


def card_value(card):
    rank = card[:-1]

    if rank in ["J", "Q", "K"]:
        return 10

    if rank == "A":
        return 11

    return int(rank)


def hand_value(hand):
    total = 0
    aces = 0

    for card in hand:
        total += card_value(card)

        if card[:-1] == "A":
            aces += 1

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


@gamble_bp.route("/gamble")
def gamble():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    if not session.get("gamble_unlocked"):
        return render_template_string(
            GAMBLE_LOGIN_HTML,
            error=None
        )

    if "gamble_balance" not in session:
        session["gamble_balance"] = 1000

    return render_template_string(
        GAMBLE_HTML,
        balance=session["gamble_balance"]
    )


@gamble_bp.route("/gamble/unlock", methods=["POST"])
def unlock_gamble():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    code = request.form.get("gamble_code", "").strip()

    if code != GAMBLE_CODE:
        return render_template_string(
            GAMBLE_LOGIN_HTML,
            error="Incorrect casino code."
        )

    session["gamble_unlocked"] = True

    if "gamble_balance" not in session:
        session["gamble_balance"] = 1000

    return redirect(url_for("gamble.gamble"))


@gamble_bp.route("/gamble/logout", methods=["POST"])
def gamble_logout():
    session.clear()
    return redirect(url_for("study"))


@gamble_bp.route("/gamble/blackjack")
def blackjack():
    if not check_gamble_access():
        return redirect(url_for("gamble.gamble"))

    if "gamble_balance" not in session:
        session["gamble_balance"] = 1000

    return render_template_string(
        BLACKJACK_HTML,
        balance=session["gamble_balance"],
        game_started=False,
        dealer_cards=[],
        player_cards=[],
        player_total=0,
        dealer_total=None,
        bet=0,
        message=None,
        active=False
    )


@gamble_bp.route("/gamble/blackjack/start", methods=["POST"])
def blackjack_start():
    if not check_gamble_access():
        return redirect(url_for("gamble.gamble"))

    try:
        bet = int(request.form.get("bet", "0"))
    except:
        bet = 0

    balance = session.get("gamble_balance", 1000)

    if bet <= 0 or bet > balance:
        return render_template_string(
            BLACKJACK_HTML,
            balance=balance,
            game_started=False,
            dealer_cards=[],
            player_cards=[],
            player_total=0,
            dealer_total=None,
            bet=0,
            message="Invalid bet.",
            active=False
        )

    deck = create_deck()

    player_cards = [
        deck.pop(),
        deck.pop()
    ]

    dealer_cards = [
        deck.pop(),
        deck.pop()
    ]

    session["gamble_balance"] = balance - bet

    game = {
        "deck": deck,
        "player_cards": player_cards,
        "dealer_cards": dealer_cards,
        "bet": bet,
        "active": True
    }

    player_total = hand_value(player_cards)

    if player_total == 21:
        session["gamble_balance"] += bet * 2
        game["active"] = False
        session["blackjack"] = game

        return render_template_string(
            BLACKJACK_HTML,
            balance=session["gamble_balance"],
            game_started=True,
            dealer_cards=dealer_cards,
            player_cards=player_cards,
            player_total=player_total,
            dealer_total=hand_value(dealer_cards),
            bet=bet,
            message="Blackjack! You win!",
            active=False
        )

    session["blackjack"] = game

    return render_template_string(
        BLACKJACK_HTML,
        balance=session["gamble_balance"],
        game_started=True,
        dealer_cards=[dealer_cards[0], "❓"],
        player_cards=player_cards,
        player_total=player_total,
        dealer_total=None,
        bet=bet,
        message=None,
        active=True
    )


@gamble_bp.route("/gamble/blackjack/hit", methods=["POST"])
def blackjack_hit():
    if not check_gamble_access():
        return redirect(url_for("gamble.gamble"))

    game = session.get("blackjack")

    if not game or not game.get("active"):
        return redirect(url_for("gamble.blackjack"))

    game["player_cards"].append(game["deck"].pop())

    player_total = hand_value(game["player_cards"])

    if player_total > 21:
        game["active"] = False
        session["blackjack"] = game

        return render_template_string(
            BLACKJACK_HTML,
            balance=session["gamble_balance"],
            game_started=True,
            dealer_cards=game["dealer_cards"],
            player_cards=game["player_cards"],
            player_total=player_total,
            dealer_total=hand_value(game["dealer_cards"]),
            bet=game["bet"],
            message="Bust! You lose.",
            active=False
        )

    session["blackjack"] = game

    return render_template_string(
        BLACKJACK_HTML,
        balance=session["gamble_balance"],
        game_started=True,
        dealer_cards=[game["dealer_cards"][0], "❓"],
        player_cards=game["player_cards"],
        player_total=player_total,
        dealer_total=None,
        bet=game["bet"],
        message=None,
        active=True
    )


@gamble_bp.route("/gamble/blackjack/stand", methods=["POST"])
def blackjack_stand():
    if not check_gamble_access():
        return redirect(url_for("gamble.gamble"))

    game = session.get("blackjack")

    if not game or not game.get("active"):
        return redirect(url_for("gamble.blackjack"))

    while hand_value(game["dealer_cards"]) < 17:
        game["dealer_cards"].append(game["deck"].pop())

    player_total = hand_value(game["player_cards"])
    dealer_total = hand_value(game["dealer_cards"])
    bet = game["bet"]

    if dealer_total > 21:
        message = "Dealer busts! You win!"
        session["gamble_balance"] += bet * 2
    elif player_total > dealer_total:
        message = "You win!"
        session["gamble_balance"] += bet * 2
    elif player_total < dealer_total:
        message = "Dealer wins!"
    else:
        message = "Push! Your bet is returned."
        session["gamble_balance"] += bet

    game["active"] = False
    session["blackjack"] = game

    return render_template_string(
        BLACKJACK_HTML,
        balance=session["gamble_balance"],
        game_started=True,
        dealer_cards=game["dealer_cards"],
        player_cards=game["player_cards"],
        player_total=player_total,
        dealer_total=dealer_total,
        bet=bet,
        message=message,
        active=False
    )
