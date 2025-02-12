import sys
# Ensure stdout is UTF-8 encoded (to support emojis)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import time
import os
import threading
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Telegram imports for python-telegram-bot v20+
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load environment variables from .env file
load_dotenv()

# Global configuration (update placeholders as needed)
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Load recipient chat IDs from an environment variable (comma-separated).
# For example: "7044485421,-1001234567890" where the channel id starts with -100.
recipient_ids_env = os.getenv("RECIPIENT_CHAT_IDS")
if recipient_ids_env:
    RECIPIENT_CHAT_IDS = [cid.strip() for cid in recipient_ids_env.split(",")]
else:
    RECIPIENT_CHAT_IDS = ["TELEGRAM_CHAT_ID"]

# Debug: print loaded credentials (remove or comment out in production)
print("DEBUG: Loaded Credentials")
print("TronGrid API Key:", TRONGRID_API_KEY)
print("Telegram Bot Token:", TELEGRAM_BOT_TOKEN)
print("Recipient Chat IDs:", RECIPIENT_CHAT_IDS)

# Global data structures and thread lock
data_lock = threading.Lock()
tracked_wallets = {
    "MainWallet": "TEYQfA5LfWLVCFZjSPvEAoQcHvWKJFz3G3"  # TRX wallet address being tracked
}
processed_transactions = set()

# List of known exchange wallet addresses (update with real addresses if needed)
exchange_wallets = [
    "TBinanceWallet123...",
    "TBitgetWallet456...",
    "TKuCoinWallet789..."
]

def send_telegram_alert(message):
    """
    Sends a Telegram alert message to all specified chat IDs.
    """
    print("DEBUG: Attempting to send Telegram alert:")
    print(message)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in RECIPIENT_CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload)
            print(f"DEBUG: Sent to {chat_id}: {response.status_code} {response.text}")
        except Exception as e:
            print(f"ERROR: Exception while sending alert to {chat_id}: {e}")

def get_wallet_transactions(wallet_address, limit=10):
    """
    Fetches recent transactions for a given TRX wallet from TronGrid.
    """
    url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions?limit={limit}"
    headers = {"TRON-PRO-API-KEY": TRONGRID_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("data", [])
            print(f"DEBUG: Fetched {len(data)} transactions for wallet {wallet_address}")
            return data
        else:
            print(f"ERROR: Fetching transactions for {wallet_address} returned status {response.status_code}")
            print("Response:", response.text)
            return []
    except Exception as e:
        print("ERROR: Exception in get_wallet_transactions:", e)
        return []

def format_timestamp(ts):
    """
    Converts a timestamp (in milliseconds) to a formatted string in UTC+1.
    """
    try:
        dt_utc = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        dt_local = dt_utc.astimezone(timezone(timedelta(hours=1)))
        return dt_local.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print("ERROR: Exception formatting timestamp:", e)
        return "Unknown time"

def track_wallet_transactions():
    """
    Polls the TronGrid API for new transactions and sends alerts only for new transactions.
    """
    while True:
        with data_lock:
            wallets_copy = tracked_wallets.copy()
        for wallet_name, wallet_address in wallets_copy.items():
            transactions = get_wallet_transactions(wallet_address)
            for tx in transactions:
                tx_id = tx.get("txID")
                # Use block_timestamp if available; otherwise, fallback to raw_data timestamp
                tx_timestamp = tx.get("block_timestamp") or tx.get("raw_data", {}).get("timestamp", 0)
                formatted_time = format_timestamp(tx_timestamp) if tx_timestamp else "Unknown time"
                try:
                    contract = tx["raw_data"]["contract"][0]
                    parameter_value = contract["parameter"]["value"]
                    sender = parameter_value.get("owner_address", "Unknown")
                    receiver = parameter_value.get("to_address", "Unknown")
                    # Convert amount from SUN (1 TRX = 1,000,000 SUN)
                    amount = parameter_value.get("amount", 0) / 1_000_000
                except Exception as e:
                    print("ERROR: Exception processing transaction:", e)
                    continue

                with data_lock:
                    if tx_id and tx_id in processed_transactions:
                        continue  # Skip already processed transactions
                    else:
                        processed_transactions.add(tx_id)

                alert_message = f"🚨 *New Transaction Detected!*\n\n"
                alert_message += f"🔹 *Wallet:* {wallet_name}\n"
                alert_message += f"🔹 *Amount:* {amount} TRX\n"
                alert_message += f"🔹 *From:* `{sender}`\n"
                alert_message += f"🔹 *To:* `{receiver}`\n"
                alert_message += f"🔹 *Date & Time (UTC+1):* {formatted_time}\n"
                alert_message += f"🔹 [View on Tronscan](https://tronscan.org/#/transaction/{tx_id})"
                if sender in exchange_wallets or receiver in exchange_wallets:
                    alert_message += "\n\n⚠️ *Alert: This transaction involves an Exchange Wallet!* ⚠️"
                send_telegram_alert(alert_message)
                print(f"DEBUG: New transaction for {wallet_name} - {amount} TRX from {sender} to {receiver} at {formatted_time}")
        print("DEBUG: Waiting 5 seconds before next check...")
        time.sleep(5)

# ----------------- Telegram Command Handlers (Async) -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Welcome to the TRX Wallet Tracker Bot!\n\n"
        "Available commands:\n"
        "/addwallet <name> <address> - Add a wallet to track\n"
        "/removewallet <name> - Remove a tracked wallet\n"
        "/listwallets - List all tracked wallets\n"
        "/history <wallet_name> - View recent transactions for a wallet\n"
    )
    await update.message.reply_text(message)

async def addwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /addwallet <name> <address>")
            return
        wallet_name = args[0]
        wallet_address = args[1]
        with data_lock:
            tracked_wallets[wallet_name] = wallet_address
        await update.message.reply_text(f"Wallet '{wallet_name}' added for tracking.")
    except Exception as e:
        await update.message.reply_text(f"Error adding wallet: {e}")

async def removewallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Usage: /removewallet <name>")
            return
        wallet_name = args[0]
        with data_lock:
            if wallet_name in tracked_wallets:
                del tracked_wallets[wallet_name]
                await update.message.reply_text(f"Wallet '{wallet_name}' removed from tracking.")
            else:
                await update.message.reply_text(f"Wallet '{wallet_name}' not found.")
    except Exception as e:
        await update.message.reply_text(f"Error removing wallet: {e}")

async def listwallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with data_lock:
        if not tracked_wallets:
            await update.message.reply_text("No wallets are currently being tracked.")
        else:
            message = "Tracked Wallets:\n"
            for name, addr in tracked_wallets.items():
                message += f"- *{name}*: `{addr}`\n"
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Usage: /history <wallet_name>")
            return
        wallet_name = args[0]
        with data_lock:
            wallet_address = tracked_wallets.get(wallet_name)
        if not wallet_address:
            await update.message.reply_text(f"Wallet '{wallet_name}' not found.")
            return
        # Fetch the last 5 transactions for the requested wallet
        transactions = get_wallet_transactions(wallet_address, limit=5)
        if not transactions:
            await update.message.reply_text("No transactions found.")
            return
        message = f"Recent transactions for *{wallet_name}*:\n\n"
        for tx in transactions:
            tx_id = tx.get("txID", "N/A")
            tx_timestamp = tx.get("block_timestamp") or tx.get("raw_data", {}).get("timestamp", 0)
            formatted_time = format_timestamp(tx_timestamp) if tx_timestamp else "Unknown time"
            try:
                contract = tx["raw_data"]["contract"][0]
                parameter_value = contract["parameter"]["value"]
                sender = parameter_value.get("owner_address", "Unknown")
                receiver = parameter_value.get("to_address", "Unknown")
                amount = parameter_value.get("amount", 0) / 1_000_000
            except Exception:
                continue
            message += (
                f"• *Amount:* {amount} TRX\n"
                f"  *From:* `{sender}`\n"
                f"  *To:* `{receiver}`\n"
                f"  *Date & Time (UTC+1):* {formatted_time}\n"
                f"  [View on Tronscan](https://tronscan.org/#/transaction/{tx_id})\n\n"
            )
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Error retrieving history: {e}")

# ----------------- Main Function: Start Tracker and Telegram Bot -----------------

def main():
    # Start the transaction tracking loop in a separate daemon thread
    tracking_thread = threading.Thread(target=track_wallet_transactions, daemon=True)
    tracking_thread.start()

    # Build and configure the Telegram bot application (v20+)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addwallet", addwallet))
    app.add_handler(CommandHandler("removewallet", removewallet))
    app.add_handler(CommandHandler("listwallets", listwallets))
    app.add_handler(CommandHandler("history", history))

    print("DEBUG: Starting Telegram bot polling...")
    app.run_polling()

if __name__ == "__main__":
    print("Starting TRX Wallet Tracker Bot...")
    main()
