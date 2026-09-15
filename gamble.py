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

DRIVE_FILE_ID = os.environ.get("GOOGLE_DRIVE_FILE_ID")
DRIVE_LOCK = threading.Lock()


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
    with DRIVE_LOCK:
        accounts_data = load_accounts()
        account = accounts_data.get("accounts", {}).get(account_name)

        if not account:
            return None

        used = int(account.get("characters_used", 0))
        maximum = int(account.get("characters_max", 0))

        if amount < 0:
            cost = -amount

            if maximum - used < cost:
                return None

            account["characters_used"] = used + cost
        else:
            account["characters_used"] = used - amount

        save_accounts(accounts_data)

        return max(
            0,
            int(account.get("characters_max", 0)) - int(account.get("characters_used", 0))
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


def is_soft_hand(hand):
    total = 0
    aces = 0

    for card in hand:
        total += card_value(card)

        if card[:-1] == "A":
            aces += 1

    return aces > 0 and total <= 21


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
        .number { font-size: 70px; font-weight: bold; margin: 25px; }
        .balance { font-size: 20px; color: #fbbf24; font-weight: bold; }
        input, select { padding: 12px; border: none; border-radius: 8px; font-size: 16px; margin: 5px; }
        button { padding: 12px 20px; border: none; border-radius: 8px; background: #fbbf24; color: #111827; font-weight: bold; cursor: pointer; margin: 5px; }
        .message { font-size: 22px; font-weight: bold; margin: 20px 0; }
        .error { color: #fecaca; font-weight: bold; }
        .rules { margin-top: 25px; color: #bbf7d0; font-size: 14px; line-height: 1.6; }
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
        {% if number is not none %}<div class="number">{{ number }}</div>{% else %}<div class="number">?</div>{% endif %}
        {% if message %}<div class="message">{{ message }}</div>{% endif %}
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/gamble/roulette/spin">
            <p>Bet how many credits?</p>
            <input type="number" name="bet" min="1" max="{{ balance }}" required>
            <p>What do you want to bet on?</p>
            <select name="bet_type" id="bet_type" onchange="toggleNumber()">
                <option value="red">Red</option>
                <option value="black">Black</option>
                <option value="odd">Odd</option>
                <option value="even">Even</option>
                <option value="number">Specific Number</option>
            </select>
            <input type="number" name="number_bet" id="number_bet" min="0" max="36" placeholder="0-36" style="display:none;">
            <br><button type="submit">Spin Roulette</button>
        </form>
        <div class="rules">Red/Black and Odd/Even pay 2× your bet. A correct number pays 35×. 0 is green and loses red/black and odd/even bets.</div>
    </div>
</div>
<script>
function toggleNumber() {
    document.getElementById('number_bet').style.display = document.getElementById('bet_type').value === 'number' ? 'inline-block' : 'none';
}
</script>
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
        return render_template_string(ROULETTE_HTML, balance=balance, number=None, message=None, error="Invalid bet.")

    if bet_type not in ["red", "black", "odd", "even", "number"]:
        return render_template_string(ROULETTE_HTML, balance=balance, number=None, message=None, error="Invalid bet type.")

    if bet_type == "number" and not 0 <= number_bet <= 36:
        return render_template_string(ROULETTE_HTML, balance=balance, number=None, message=None, error="Choose a number from 0 to 36.")

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
        message=message,
        error=None
    )


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
