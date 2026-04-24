import requests
import time
from telegram import Bot

# =========================
# AYARLAR
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

API_KEY = os.getenv("API_KEY")
URL = "https://api.nansen.ai/api/v1/token-screener"

bot = Bot(token=TELEGRAM_TOKEN)

seen = set()

# =========================
# NANSEN API
# =========================
def get_tokens():
    headers = {
        "Content-Type": "application/json",
        "apiKey": API_KEY
    }

    payload = {
        "chains": ["ethereum", "solana"],  # istersen solana da ekle
        "timeframe": "10m",
        "filters": {
            "only_smart_money": True,
            "token_age_days": {
                "max": 1,
                "min": 0
            }
        },
        "order_by": [
            {
                "field": "buy_volume",
                "direction": "DESC"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 50
        }
    }

    try:
        res = requests.post(URL, headers=headers, json=payload, timeout=10)
        data = res.json()
    except Exception as e:
        print("API hata:", e)
        return []

    return data


# =========================
# PARSE
# =========================
def parse(data):
    tokens = []

    results = data.get("data", [])  # çoğunlukla buradan gelir

    for item in results:
        try:
            symbol = item.get("symbol")
            address = item.get("address") or item.get("token_address")
            smart_wallets = item.get("smart_money_count", 0)
            buy_volume = item.get("buy_volume", 0)

            if not address:
                continue

            # SENİN ŞARTIN
            if smart_wallets >= 3:
                tokens.append({
                    "symbol": symbol,
                    "address": address,
                    "smart_wallets": smart_wallets,
                    "volume": buy_volume
                })

        except:
            continue

    return tokens


# =========================
# TELEGRAM
# =========================
def send(token):
    msg = f"""
🚀 NANSEN SIGNAL

Symbol: {token['symbol']}
Smart Wallets: {token['smart_wallets']}
Volume: ${int(token['volume'])}

https://dexscreener.com/ethereum/{token['address']}
"""
    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print("Telegram hata:", e)


# =========================
# LOOP
# =========================
def main():
    print("Bot başladı...")

    while True:
        data = get_tokens()
        tokens = parse(data)

        for t in tokens:
            if t["address"] not in seen:
                send(t)
                seen.add(t["address"])

        time.sleep(60)


if __name__ == "__main__":
    main()
