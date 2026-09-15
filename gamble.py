from flask import Blueprint, session, redirect, url_for, render_template_string, request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import os
import json
import io
import random
import threading


gamble_bp = Blueprint("gamble", __name__)
GAMES_CODE = "2468"

from storage import load_accounts, change_account_credits, LOCK as DRIVE_LOCK


def get_current_account():
    if not session.get("logged_in") or session.get("admin"):
        return None, None

    account_name = session.get("account_name")

    if not account_name:
        return None, None

    with DRIVE_LOCK:
        accounts_data = load_accounts()
        account = accounts_data.get("accounts", {}).get(account_name)

    if not account:
        return None, None

    return account_name, account


def get_credits(account):
    maximum = int(account.get("characters_max", 0))
    used = int(account.get("characters_used", 0))
    return max(0, maximum - used)


def change_credits(account_name, amount):
    return change_account_credits(account_name, amount)


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


def is_soft_hand(hand):
    total = 0
    aces = 0

    for card in hand:
        total += card_value(card)

        if card[:-1] == "A":
            aces += 1

    return aces > 0 and total <= 21


GAMES_CODE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Games Access - StudySpace</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #111827; color: white; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .box { width: min(420px, 90%); background: #1f2937; border-radius: 18px; padding: 35px; text-align: center; box-shadow: 0 15px 40px rgba(0,0,0,.35); }
        h1 { margin-top: 0; }
        p { color: #9ca3af; }
        input { width: 100%; padding: 14px; border: none; border-radius: 8px; font-size: 20px; text-align: center; margin: 15px 0; }
        button { width: 100%; padding: 13px; border: none; border-radius: 8px; background: #2563eb; color: white; font-weight: bold; font-size: 16px; cursor: pointer; }
        .error { color: #fca5a5; font-weight: bold; margin-bottom: 12px; }
        .back { display: inline-block; margin-top: 18px; color: #93c5fd; text-decoration: none; }
    </style>
</head>
<body>
<div class="box">
    <h1>🎮 Games</h1>
    <p>Enter the games access code to continue.</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST" action="/gamble/code">
        <input type="password" name="code" inputmode="numeric" maxlength="4" placeholder="Access code" required autofocus>
        <button type="submit">Enter Games</button>
    </form>
    <a class="back" href="/study">← Back to StudySpace</a>
</div>
</body>
</html>
"""


CASINO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Casino - StudySpace</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #111827; color: white; }
        .top { background: #1f2937; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #374151; }
        .top a { text-decoration: none; color: white; font-weight: bold; }
        .logout { background: #dc2626; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .container { max-width: 1000px; margin: 40px auto; padding: 20px; }
        .header { background: #1f2937; border-radius: 18px; padding: 30px; margin-bottom: 25px; text-align: center; }
        .header h1 { margin: 0 0 10px; font-size: 36px; }
        .balance { font-size: 20px; font-weight: bold; color: #fbbf24; }
        .games { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 18px; }
        .game { background: #1f2937; border-radius: 16px; padding: 25px; text-align: center; }
        .game-icon { font-size: 45px; margin-bottom: 15px; }
        .game h2 { margin: 0 0 10px; }
        .game p { color: #9ca3af; }
        .play { display: inline-block; margin-top: 10px; padding: 10px 16px; background: #2563eb; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .coming { display: inline-block; margin-top: 10px; padding: 10px 16px; background: #374151; color: #9ca3af; border-radius: 8px; font-weight: bold; }
    </style>
</head>
<body>
<div class="top">
    <a href="/study">← Back to AI</a>
    <form method="POST" action="/gamble/logout">
        <button class="logout" type="submit">Log Out</button>
    </form>
</div>
<div class="container">
    <div class="header">
        <h1>🎰 Casino</h1>
        <p>Use your StudySpace credits.</p>
        <div class="balance">Credits: {{ balance }}</div>
    </div>
    <div class="games">
        <div class="game">
            <div class="game-icon">🃏</div>
            <h2>Blackjack</h2>
            <p>Try to beat the dealer.</p>
            <a class="play" href="/gamble/blackjack">Play Blackjack</a>
        </div>
        <div class="game">
            <div class="game-icon">🎰</div>
            <h2>Slots</h2>
            <p>Spin the reels and try your luck.</p>
            <a class="play" href="/gamble/slots">Play Slots</a>
        </div>
        <div class="game">
            <div class="game-icon">🎡</div>
            <h2>Roulette</h2>
            <p>Pick a number or bet on a color.</p>
            <a class="play" href="/gamble/roulette">Play Roulette</a>
        </div>
        <div class="game">
            <div class="game-icon">🃏</div>
            <h2>Poker</h2>
            <p>Hold cards and make the best five-card hand.</p>
            <a class="play" href="/gamble/poker">Play Poker</a>
        </div>
    </div>
</div>
</body>
</html>
"""


SLOTS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Slots - StudySpace</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #312e81; color: white; }
        .top { background: #1e1b4b; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }
        .top a { color: white; text-decoration: none; font-weight: bold; }
        .logout { background: #dc2626; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .container { max-width: 800px; margin: 35px auto; padding: 20px; }
        .machine { background: #4338ca; border-radius: 20px; padding: 35px; text-align: center; }
        .balance { font-size: 20px; color: #fbbf24; font-weight: bold; }
        .reels { display: flex; justify-content: center; gap: 12px; margin: 35px 0; flex-wrap: wrap; }
        .reel { width: 120px; height: 120px; background: white; color: #111827; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 55px; }
        input, select { padding: 12px; border: none; border-radius: 8px; font-size: 16px; }
        button { padding: 12px 20px; border: none; border-radius: 8px; background: #fbbf24; color: #111827; font-weight: bold; cursor: pointer; margin: 5px; }
        .message { font-size: 22px; font-weight: bold; margin: 20px 0; }
        .error { color: #fecaca; font-weight: bold; }
        .payouts { margin-top: 25px; color: #ddd6fe; font-size: 14px; }
    </style>
</head>
<body>
<div class="top">
    <a href="/gamble">← Back to Casino</a>
    <form method="POST" action="/gamble/logout"><button class="logout" type="submit">Log Out</button></form>
</div>
<div class="container">
    <div class="machine">
        <h1>🎰 Slots</h1>
        <div class="balance">Credits: {{ balance }}</div>
        <div class="reels">
            {% for symbol in reels %}<div class="reel">{{ symbol }}</div>{% endfor %}
        </div>
        {% if message %}<div class="message">{{ message }}</div>{% endif %}
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/gamble/slots/spin">
            <p>Bet how many credits?</p>
            <input type="number" name="bet" min="1" max="{{ balance }}" required>
            <br><button type="submit">Spin</button>
        </form>
        <div class="payouts">Three 7s: 10× · Three matching symbols: 5× · Two matching symbols: 1.5×</div>
    </div>
</div>
</body>
</html>
"""

ROULETTE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Roulette - StudySpace</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #14532d; color: white; }
        .top { background: #052e16; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }
        .top a { color: white; text-decoration: none; font-weight: bold; }
        .logout { background: #dc2626; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .container { max-width: 850px; margin: 35px auto; padding: 20px; }
        .wheel { background: #166534; border-radius: 20px; padding: 35px; text-align: center; }
        .number { font-size: 70px; font-weight: bold; margin: 25px 0 10px; }
        .red { color: #f87171; }
        .black { color: #111827; background: white; display: inline-block; padding: 4px 14px; border-radius: 10px; }
        .green { color: #4ade80; }
        .result-label { font-size: 22px; font-weight: bold; margin-bottom: 20px; }
        .balance { font-size: 20px; color: #fbbf24; font-weight: bold; }
        input, select { padding: 12px; border: none; border-radius: 8px; font-size: 16px; margin: 5px; }
        button { padding: 12px 20px; border: none; border-radius: 8px; background: #fbbf24; color: #111827; font-weight: bold; cursor: pointer; margin: 5px; }
        .message { font-size: 22px; font-weight: bold; margin: 20px 0; }
        .error { color: #fecaca; font-weight: bold; }
        .payouts { margin-top: 25px; color: #bbf7d0; font-size: 14px; }
    </style>
</head>
<body>
<div class="top">
    <a href="/gamble">← Back to Casino</a>
    <form method="POST" action="/gamble/logout"><button class="logout" type="submit">Log Out</button></form>
</div>
<div class="container">
    <div class="wheel">
        <h1>🎡 Roulette</h1>
        <div class="balance">Credits: {{ balance }}</div>
        {% if number is not none %}
            <div class="number {{ result_color_class }}">{{ number }}</div>
            <div class="result-label">Landed on {{ result_color }}{% if number == 0 %} · Green{% endif %}</div>
        {% else %}
            <div class="number">?</div>
        {% endif %}
        {% if message %}<div class="message">{{ message }}</div>{% endif %}
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/gamble/roulette/spin">
            <p>Bet how many credits?</p>
            <input type="number" name="bet" min="1" max="{{ balance }}" required>
            <br>
            <select name="bet_type" onchange="document.getElementById('numberBet').style.display = this.value === 'number' ? 'inline-block' : 'none'">
                <option value="red">Red</option>
                <option value="black">Black</option>
                <option value="odd">Odd</option>
                <option value="even">Even</option>
                <option value="number">Specific Number</option>
            </select>
            <input id="numberBet" style="display:none" type="number" name="number_bet" min="0" max="36" placeholder="0-36">
            <br><button type="submit">Spin Roulette</button>
        </form>
        <div class="payouts">Red/Black/Odd/Even: 2× total payout · Specific number: 36× total payout</div>
    </div>
</div>
</body>
</html>
"""

POKER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Poker - StudySpace</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #172554; color: white; }
        .top { background: #0f172a; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }
        .top a { color: white; text-decoration: none; font-weight: bold; }
        .logout { background: #dc2626; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .container { max-width: 1000px; margin: 35px auto; padding: 20px; }
        .table { background: #1e3a8a; border-radius: 22px; padding: 35px; text-align: center; }
        .balance { font-size: 20px; color: #fbbf24; font-weight: bold; }
        .cards { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin: 30px 0 10px; }
        .card-wrap { width: 125px; }
        .card { height: 170px; background: white; color: #111827; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 34px; font-weight: bold; border: 4px solid transparent; }
        .card.red-card { color: #dc2626; }
        .card.held { border-color: #fbbf24; transform: translateY(-8px); }
        .hold { margin-top: 8px; padding: 9px 14px; }
        .message { font-size: 22px; font-weight: bold; margin: 20px 0; }
        .error { color: #fecaca; font-weight: bold; }
        input { padding: 12px; border: none; border-radius: 8px; font-size: 16px; }
        button { padding: 12px 20px; border: none; border-radius: 8px; background: #fbbf24; color: #111827; font-weight: bold; cursor: pointer; margin: 5px; }
        .payouts { margin-top: 25px; color: #bfdbfe; font-size: 14px; line-height: 1.8; }
        .held-note { color: #fde68a; font-weight: bold; }
    </style>
</head>
<body>
<div class="top">
    <a href="/gamble">← Back to Casino</a>
    <form method="POST" action="/gamble/logout"><button class="logout" type="submit">Log Out</button></form>
</div>
<div class="container">
    <div class="table">
        <h1>🃏 Poker</h1>
        <div class="balance">Credits: {{ balance }}</div>
        {% if game_started %}
            <div class="cards">
                {% for card in cards %}
                    <div class="card-wrap">
                        <div class="card {% if card[-1] in ['♥','♦'] %}red-card{% endif %} {% if loop.index0 in held %}held{% endif %}">{{ card }}</div>
                        {% if active %}
                            <form method="POST" action="/gamble/poker/hold">
                                <input type="hidden" name="index" value="{{ loop.index0 }}">
                                <button class="hold" type="submit">{% if loop.index0 in held %}Held{% else %}Hold{% endif %}</button>
                            </form>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
            {% if active %}<div class="held-note">Held: {{ held|length }}/5</div>{% endif %}
        {% endif %}
        {% if message %}<div class="message">{{ message }}</div>{% endif %}
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if not game_started or not active %}
            <form method="POST" action="/gamble/poker/start">
                <p>Bet how many credits?</p>
                <input type="number" name="bet" min="1" max="{{ balance }}" required>
                <br><button type="submit">Deal 5 Cards</button>
            </form>
        {% else %}
            <form method="POST" action="/gamble/poker/draw">
                <button type="submit">Draw</button>
            </form>
        {% endif %}
        <div class="payouts">
            3 of a Kind: 2× · Straight: 3× · Flush: 4× · Full House: 5×<br>
            4 of a Kind: 7× · Straight Flush: 8× · Royal Flush: 10×<br>
            Pair, Two Pair, or High Card: Lose your bet
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
        body { margin: 0; font-family: Arial, sans-serif; background: #064e3b; color: white; }
        .top { background: #022c22; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }
        .top a { color: white; text-decoration: none; font-weight: bold; }
        .logout { background: #dc2626; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .container { max-width: 900px; margin: 35px auto; padding: 20px; }
        .table { background: #047857; border-radius: 20px; padding: 30px; min-height: 500px; text-align: center; }
        .balance { font-size: 20px; color: #fbbf24; font-weight: bold; }
        .section { margin: 30px 0; }
        .cards { display: flex; justify-content: center; flex-wrap: wrap; gap: 12px; margin: 15px 0; }
        .card { width: 75px; height: 105px; background: white; color: black; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: bold; }
        .bet { margin: 25px 0; }
        .bet input { padding: 12px; width: 160px; border: none; border-radius: 8px; font-size: 16px; }
        button { padding: 12px 18px; border: none; border-radius: 8px; background: #fbbf24; color: #111827; font-weight: bold; cursor: pointer; margin: 5px; }
        .message { font-size: 22px; font-weight: bold; margin: 25px 0; }
        .error { color: #fecaca; font-weight: bold; }
        .note { color: #d1fae5; font-size: 13px; margin-top: 20px; }
    </style>
</head>
<body>
<div class="top">
    <a href="/gamble">← Back to Casino</a>
    <form method="POST" action="/gamble/logout">
        <button class="logout" type="submit">Log Out</button>
    </form>
</div>
<div class="container">
    <div class="table">
        <h1>🃏 Blackjack</h1>
        <div class="balance">Credits: {{ balance }}</div>

        {% if not game_started %}
            <div class="bet">
                <form method="POST" action="/gamble/blackjack/start">
                    <p>How many credits do you want to bet?</p>
                    <input type="number" name="bet" min="1" max="{{ balance }}" required>
                    <br>
                    <button type="submit">Deal</button>
                </form>
            </div>
            {% if message %}
                <div class="message">{{ message }}</div>
            {% endif %}
        {% else %}
            <div class="section">
                <h2>Dealer</h2>
                <div class="cards">
                    {% for card in dealer_cards %}
                        <div class="card">{{ card }}</div>
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
                        <div class="card">{{ card }}</div>
                    {% endfor %}
                </div>
                <p>Total: {{ player_total }}</p>
            </div>

            <p>Bet: {{ bet }}</p>

            {% if message %}
                <div class="message">{{ message }}</div>
            {% endif %}

            {% if active %}
                <form method="POST" action="/gamble/blackjack/hit">
                    <button type="submit">Hit</button>
                </form>
                <form method="POST" action="/gamble/blackjack/stand">
                    <button type="submit">Stand</button>
                </form>
            {% else %}
                <a href="/gamble/blackjack">
                    <button type="button">Play Again</button>
                </a>
            {% endif %}
        {% endif %}

        <div class="note">Your casino credits are your normal StudySpace credits.</div>
    </div>
</div>
</body>
</html>
"""


@gamble_bp.before_request
def require_games_code():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    if request.endpoint in {"gamble.games_code", "gamble.games_logout"}:
        return None

    if not session.get("games_access"):
        return redirect(url_for("gamble.games_code"))

    return None


@gamble_bp.route("/gamble/code", methods=["GET", "POST"])
def games_code():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    if session.get("games_access"):
        return redirect(url_for("gamble.gamble"))

    error = None

    if request.method == "POST":
        code = request.form.get("code", "").strip()

        if code == GAMES_CODE:
            session["games_access"] = True
            session.pop("games_code_error", None)
            return redirect(url_for("gamble.gamble"))

        error = "Incorrect access code."

    return render_template_string(GAMES_CODE_HTML, error=error)


@gamble_bp.route("/gamble/games-logout", methods=["POST"])
def games_logout():
    session.pop("games_access", None)
    session.pop("blackjack", None)
    session.pop("poker", None)
    return redirect(url_for("study"))


@gamble_bp.route("/gamble")
def gamble():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    _, account = get_current_account()

    if not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)

    return render_template_string(
        CASINO_HTML,
        balance=balance
    )


@gamble_bp.route("/gamble/logout", methods=["POST"])
def gamble_logout():
    session.clear()
    return redirect(url_for("study"))


@gamble_bp.route("/gamble/slots")
def slots():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    _, account = get_current_account()
    if not account:
        session.clear()
        return redirect(url_for("study"))

    return render_template_string(
        SLOTS_HTML,
        balance=get_credits(account),
        reels=["❔", "❔", "❔"],
        message=None,
        error=None
    )


@gamble_bp.route("/gamble/slots/spin", methods=["POST"])
def slots_spin():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()
    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)

    try:
        bet = int(request.form.get("bet", "0"))
    except:
        bet = 0

    if bet <= 0 or bet > balance:
        return render_template_string(SLOTS_HTML, balance=balance, reels=["❔", "❔", "❔"], message=None, error="Invalid bet.")

    new_balance = change_credits(account_name, -bet)
    if new_balance is None:
        return redirect(url_for("gamble.slots"))

    symbols = ["🍒", "🍋", "🍊", "🔔", "⭐", "7️⃣"]
    weights = [28, 24, 20, 14, 9, 5]
    reels = random.choices(symbols, weights=weights, k=3)

    payout = 0
    if reels == ["7️⃣", "7️⃣", "7️⃣"]:
        payout = bet * 10
        message = f"JACKPOT! You won {payout:,} credits!"
    elif reels[0] == reels[1] == reels[2]:
        payout = bet * 5
        message = f"Three of a kind! You won {payout:,} credits!"
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        payout = int(bet * 1.5)
        message = f"Two match! You won {payout:,} credits!"
    else:
        message = f"No match. You lost {bet:,} credits."

    if payout:
        final_balance = change_credits(account_name, payout)
    else:
        final_balance = new_balance

    return render_template_string(
        SLOTS_HTML,
        balance=final_balance if final_balance is not None else 0,
        reels=reels,
        message=message,
        error=None
    )


def roulette_color(number):
    if number == 0:
        return "Green", "green"
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    if number in red_numbers:
        return "Red", "red"
    return "Black", "black"


@gamble_bp.route("/gamble/roulette")
def roulette():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    _, account = get_current_account()
    if not account:
        session.clear()
        return redirect(url_for("study"))

    return render_template_string(
        ROULETTE_HTML,
        balance=get_credits(account),
        number=None,
        result_color=None,
        result_color_class=None,
        message=None,
        error=None
    )


@gamble_bp.route("/gamble/roulette/spin", methods=["POST"])
def roulette_spin():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()
    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)

    try:
        bet = int(request.form.get("bet", "0"))
    except:
        bet = 0

    bet_type = request.form.get("bet_type", "red")

    try:
        number_bet = int(request.form.get("number_bet", "-1"))
    except:
        number_bet = -1

    if bet <= 0 or bet > balance:
        return render_template_string(ROULETTE_HTML, balance=balance, number=None, result_color=None, result_color_class=None, message=None, error="Invalid bet.")

    if bet_type not in ["red", "black", "odd", "even", "number"]:
        return render_template_string(ROULETTE_HTML, balance=balance, number=None, result_color=None, result_color_class=None, message=None, error="Invalid bet type.")

    if bet_type == "number" and not 0 <= number_bet <= 36:
        return render_template_string(ROULETTE_HTML, balance=balance, number=None, result_color=None, result_color_class=None, message=None, error="Choose a number from 0 to 36.")

    new_balance = change_credits(account_name, -bet)
    if new_balance is None:
        return redirect(url_for("gamble.roulette"))

    result = random.randint(0, 36)
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    won = False
    multiplier = 0

    if bet_type == "number":
        won = result == number_bet
        multiplier = 35
    elif bet_type == "red":
        won = result in red_numbers
        multiplier = 1
    elif bet_type == "black":
        won = result != 0 and result not in red_numbers
        multiplier = 1
    elif bet_type == "odd":
        won = result != 0 and result % 2 == 1
        multiplier = 1
    elif bet_type == "even":
        won = result != 0 and result % 2 == 0
        multiplier = 1

    if won:
        payout = bet * (multiplier + 1)
        final_balance = change_credits(account_name, payout)
        message = f"You won {payout:,} credits!"
    else:
        final_balance = new_balance
        message = f"You lost {bet:,} credits."

    return render_template_string(
        ROULETTE_HTML,
        balance=final_balance if final_balance is not None else 0,
        number=result,
        result_color=roulette_color(result)[0],
        result_color_class=roulette_color(result)[1],
        message=message,
        error=None
    )


def poker_rank_value(card):
    rank = card[:-1]
    values = {"J": 11, "Q": 12, "K": 13, "A": 14}
    if rank in values:
        return values[rank]
    return int(rank)


def poker_hand_result(cards):
    values = sorted([poker_rank_value(card) for card in cards])
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

    is_flush = len({card[-1] for card in cards}) == 1
    unique_values = sorted(set(values))
    is_straight = False
    if len(unique_values) == 5:
        is_straight = unique_values[-1] - unique_values[0] == 4
        if unique_values == [2, 3, 4, 5, 14]:
            is_straight = True

    if is_straight and is_flush and max(unique_values) == 14 and min(unique_values) == 10:
        return "Royal Flush", 10
    if is_straight and is_flush:
        return "Straight Flush", 8
    if 4 in counts.values():
        return "4 of a Kind", 7
    if sorted(counts.values()) == [2, 3]:
        return "Full House", 5
    if is_flush:
        return "Flush", 4
    if is_straight:
        return "Straight", 3
    if 3 in counts.values():
        return "3 of a Kind", 2
    return "No Winning Hand", 0


@gamble_bp.route("/gamble/poker")
def poker():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    _, account = get_current_account()
    if not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)
    game = session.get("poker")
    if game and game.get("active"):
        return render_template_string(
            POKER_HTML,
            balance=balance,
            game_started=True,
            cards=game.get("cards", []),
            held=game.get("held", []),
            active=True,
            message=None,
            error=None
        )

    return render_template_string(
        POKER_HTML,
        balance=balance,
        game_started=False,
        cards=[],
        held=[],
        active=False,
        message=None,
        error=None
    )


@gamble_bp.route("/gamble/poker/start", methods=["POST"])
def poker_start():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()
    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)
    try:
        bet = int(request.form.get("bet", "0"))
    except:
        bet = 0

    if bet <= 0 or bet > balance:
        return render_template_string(POKER_HTML, balance=balance, game_started=False, cards=[], held=[], active=False, message=None, error="Invalid bet.")

    new_balance = change_credits(account_name, -bet)
    if new_balance is None:
        return redirect(url_for("gamble.poker"))

    deck = create_deck()
    cards = [deck.pop() for _ in range(5)]
    session["poker"] = {
        "deck": deck,
        "cards": cards,
        "held": [],
        "bet": bet,
        "active": True
    }

    return render_template_string(POKER_HTML, balance=new_balance, game_started=True, cards=cards, held=[], active=True, message=None, error=None)


@gamble_bp.route("/gamble/poker/hold", methods=["POST"])
def poker_hold():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()
    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    game = session.get("poker")
    if not game or not game.get("active"):
        return redirect(url_for("gamble.poker"))

    try:
        index = int(request.form.get("index", "-1"))
    except:
        index = -1

    if index not in range(5):
        return redirect(url_for("gamble.poker"))

    held = game.get("held", [])
    if index in held:
        held.remove(index)
    else:
        held.append(index)
    held.sort()
    game["held"] = held
    session["poker"] = game

    balance = get_credits(account)
    return render_template_string(POKER_HTML, balance=balance, game_started=True, cards=game["cards"], held=held, active=True, message=None, error=None)


@gamble_bp.route("/gamble/poker/draw", methods=["POST"])
def poker_draw():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()
    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    game = session.get("poker")
    if not game or not game.get("active"):
        return redirect(url_for("gamble.poker"))

    held = set(game.get("held", []))
    for index in range(5):
        if index not in held:
            game["cards"][index] = game["deck"].pop()

    hand_name, multiplier = poker_hand_result(game["cards"])
    bet = int(game["bet"])
    payout = bet * multiplier if multiplier else 0

    if payout > 0:
        balance = change_credits(account_name, payout)
        message = f"{hand_name}! You won {payout:,} credits!"
    else:
        balance = get_credits(account)
        message = f"{hand_name}. You lost {bet:,} credits."

    game["active"] = False
    game["held"] = sorted(held)
    session["poker"] = game

    if balance is None:
        balance = 0

    return render_template_string(POKER_HTML, balance=balance, game_started=True, cards=game["cards"], held=game["held"], active=False, message=message, error=None)


@gamble_bp.route("/gamble/blackjack")
def blackjack():
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    _, account = get_current_account()

    if not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)

    return render_template_string(
        BLACKJACK_HTML,
        balance=balance,
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
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()

    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    balance = get_credits(account)

    try:
        bet = int(request.form.get("bet", "0"))
    except:
        bet = 0

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

    new_balance = change_credits(account_name, -bet)

    if new_balance is None:
        return redirect(url_for("gamble.blackjack"))

    deck = create_deck()

    player_cards = [deck.pop(), deck.pop()]
    dealer_cards = [deck.pop(), deck.pop()]

    game = {
        "deck": deck,
        "player_cards": player_cards,
        "dealer_cards": dealer_cards,
        "bet": bet,
        "active": True
    }

    player_total = hand_value(player_cards)
    dealer_total = hand_value(dealer_cards)

    if player_total == 21:
        payout = bet * 2
        result_balance = change_credits(account_name, payout)

        game["active"] = False
        session["blackjack"] = game

        return render_template_string(
            BLACKJACK_HTML,
            balance=result_balance,
            game_started=True,
            dealer_cards=dealer_cards,
            player_cards=player_cards,
            player_total=player_total,
            dealer_total=dealer_total,
            bet=bet,
            message="Blackjack! You win!",
            active=False
        )

    session["blackjack"] = game

    return render_template_string(
        BLACKJACK_HTML,
        balance=new_balance,
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
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()

    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    game = session.get("blackjack")

    if not game or not game.get("active"):
        return redirect(url_for("gamble.blackjack"))

    game["player_cards"].append(game["deck"].pop())

    player_total = hand_value(game["player_cards"])

    if player_total > 21:
        game["active"] = False
        session["blackjack"] = game

        balance = get_credits(account)

        return render_template_string(
            BLACKJACK_HTML,
            balance=balance,
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
    balance = get_credits(account)

    return render_template_string(
        BLACKJACK_HTML,
        balance=balance,
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
    if not session.get("logged_in") or session.get("admin"):
        return redirect(url_for("study"))

    account_name, account = get_current_account()

    if not account_name or not account:
        session.clear()
        return redirect(url_for("study"))

    game = session.get("blackjack")

    if not game or not game.get("active"):
        return redirect(url_for("gamble.blackjack"))

    while True:
        dealer_total = hand_value(game["dealer_cards"])

        if dealer_total < 17:
            game["dealer_cards"].append(game["deck"].pop())
            continue

        if dealer_total == 17 and is_soft_hand(game["dealer_cards"]):
            game["dealer_cards"].append(game["deck"].pop())
            continue

        break

    player_total = hand_value(game["player_cards"])
    dealer_total = hand_value(game["dealer_cards"])
    bet = game["bet"]

    if dealer_total > 21:
        message = "Dealer busts! You win!"
        payout = bet * 2
        balance = change_credits(account_name, payout)
    elif player_total > dealer_total:
        message = "You win!"
        payout = bet * 2
        balance = change_credits(account_name, payout)
    elif player_total < dealer_total:
        message = "Dealer wins!"
        balance = get_credits(account)
    else:
        message = "Push! Your bet is returned."
        balance = change_credits(account_name, bet)

    game["active"] = False
    session["blackjack"] = game

    if balance is None:
        balance = 0

    return render_template_string(
        BLACKJACK_HTML,
        balance=balance,
        game_started=True,
        dealer_cards=game["dealer_cards"],
        player_cards=game["player_cards"],
        player_total=player_total,
        dealer_total=dealer_total,
        bet=bet,
        message=message,
        active=False
    )
