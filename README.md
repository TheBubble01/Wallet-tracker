# 🚀 TRX Wallet Tracker Bot  

A Telegram bot that tracks TRX wallet transactions in real-time and sends alerts to multiple Telegram users and a channel. Users can dynamically add/remove wallets for tracking and request past transactions.  

## 📌 Features  

✅ Tracks multiple TRX wallets in real-time.  
✅ Sends transaction alerts to personal chats and a Telegram channel.  
✅ Allows users to add and remove wallets dynamically.  
✅ Detects and alerts when transactions involve exchange wallets (Binance, Bitget, KuCoin, etc.).  
✅ Provides a list of currently tracked wallets.  
✅ Users can request past transactions on demand.  
✅ Handles Unicode and emojis correctly.  

## 🛠️ Technologies Used  

- **Python**  
- **TronGrid API** (for fetching TRX wallet transactions)  
- **Telegram Bot API** (for sending alerts)  
- **Railway.app** (for deployment)  

## 🚀 Deployment  

The bot is deployed on **Railway.app** for continuous monitoring and execution.  

## 📖 Setup and Installation  

### 1️⃣ Clone the Repository  
\`\`\`
git clone https://github.com/TheBubble01/Wallet-tracker.git  
cd trx-wallet-tracker
\`\`\`

### 2️⃣ Create a Virtual Environment  
\`\`\`
python -m venv venv  
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

### 3️⃣ Install Dependencies  
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4️⃣ Set Up Environment Variables  

Create a \`.env\` file and add the following:  

\`\`\`
TRONGRID_API_KEY=your_trongrid_api_key  
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  
TELEGRAM_CHAT_IDS=chat_id_1,chat_id_2,channel_id  # Comma-separated list of chat IDs  
\`\`\`

### 5️⃣ Run the Bot Locally  
\`\`\`
python trx_tracker.py
\`\`\`

## 📢 Usage  

### 🔹 Start Tracking a Wallet  
Send the following command in Telegram:  
\`\`\`
/addwallet Wallet_Name WALLET_ADDRESS
\`\`\`
Example:  
\`\`\`
/addwallet Main Wallet TZHaZVFszQDvPZ5dyEAbYEuJkBwXyMdag2
\`\`\`

### 🔹 Remove a Tracked Wallet  
\`\`\`
/removewallet WALLET_ADDRESS
\`\`\`

### 🔹 List Tracked Wallets  
\`\`\`
/listwallets
\`\`\`

### 🔹 View Past Transactions of a Wallet  
\`\`\`
/history WALLET_ADDRESS
\`\`\`

## 🛠 Deployment on Railway.app  

### 1️⃣ Install Railway CLI  
\`\`\`
npm install -g @railway/cli
\`\`\`

### 2️⃣ Log in to Railway  
\`\`\`
railway login
\`\`\`

### 3️⃣ Create a New Project  
\`\`\`
railway init
\`\`\`

### 4️⃣ Set Environment Variables  
\`\`\`
railway variables set TRONGRID_API_KEY=your_api_key  
railway variables set TELEGRAM_BOT_TOKEN=your_bot_token  
railway variables set TELEGRAM_CHAT_IDS=chat_id_1,chat_id_2,channel_id
\`\`\`

### 5️⃣ Deploy the Bot  
\`\`\`
railway up
\`\`\`

## 👨‍💻 Contributions  

Feel free to fork the repository and submit a pull request with improvements!  

## 📝 License  

This project is open-source under the Apache License 2.0.  
