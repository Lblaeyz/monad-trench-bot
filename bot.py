from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import requests
import asyncio
import secrets
from web3 import Web3
from eth_account import Account

# Connect to Monad Testnet
WEB3 = Web3(Web3.HTTPProvider("https://rpc.testnet.monad.xyz"))

# In-memory watchlist and wallet store (non-persistent)
watchlist = {}
user_wallets = {}
snipes = {}

# Function to get token price and volume from Kuru API
def get_kuru_price(token_address):
    url = 'https://api.testnet.kuru.io/markets'
    try:
        resp = requests.get(url)
        data = resp.json()
        for market in data.get('markets', []):
            if market.get('baseMint', '').lower() == token_address.lower():
                return {
                    'price': market.get('price'),
                    'volume': market.get('volume24h'),
                    'liquidity': market.get('liquidityDepth'),
                    'market_id': market.get('marketId')
                }
    except Exception as e:
        print(f"Error fetching data from Kuru: {e}")
    return None

def get_token_data(token_address):
    return get_kuru_price(token_address)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📈 Chart", callback_data='chart_menu'),
            InlineKeyboardButton("💰 Wallet", callback_data='wallet_menu')
        ],
        [
            InlineKeyboardButton("🛒 Buy", callback_data='buy_menu'),
            InlineKeyboardButton("💸 Sell", callback_data='sell_menu')
        ],
        [
            InlineKeyboardButton("🎯 Snipe", callback_data='snipe_menu'),
            InlineKeyboardButton("📊 Watch", callback_data='watch_menu')
        ],
        [
            InlineKeyboardButton("🧪 Recent", callback_data='recent_menu'),
            InlineKeyboardButton("⛽️ Gas", callback_data='gas_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to MonadTrenchBot 👷🏽‍♂️\nChoose an action:",
        reply_markup=reply_markup
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'chart_menu':
        await query.edit_message_text("📈 Use /chart <token_address> to see chart data.")
    elif data == 'wallet_menu':
        await query.edit_message_text("👛 Use /createwallet or /importwallet to manage your wallet.")
    elif data == 'buy_menu':
        await query.edit_message_text("🛒 Use /buy <token_address> <amount> to buy tokens.")
    elif data == 'sell_menu':
        await query.edit_message_text("💸 Use /sell <token_address> <amount> to sell tokens.")
    elif data == 'snipe_menu':
        await query.edit_message_text("🎯 Use /snipe <token_address> <target_price> to set a sniper.")
    elif data == 'watch_menu':
        await query.edit_message_text("📊 Use /watch <token_address> <target_price> to watch prices.")
    elif data == 'recent_menu':
        await query.edit_message_text("🧪 Use /recent to check recently launched tokens.")
    elif data == 'gas_menu':
        await query.edit_message_text("⛽️ Use /gas to see Monad gas info.")

# Core wallet functions
async def create_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    acct = Account.create()
    user_wallets[user_id] = acct
    await update.message.reply_text(f"🆕 Wallet Created!\nAddress: {acct.address}\nPrivate Key (save this!): {acct.key.hex()}")

async def import_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Send your private key like this: /importwallet <private_key>")
        return
    try:
        acct = Account.from_key(args[0])
        user_wallets[user_id] = acct
        await update.message.reply_text(f"🔓 Wallet Imported!\nAddress: {acct.address}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error importing wallet: {e}")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    acct = user_wallets.get(user_id)
    if not acct:
        await update.message.reply_text("You have no wallet. Use /createwallet or /importwallet first.")
        return
    balance = WEB3.eth.get_balance(acct.address)
    eth_balance = WEB3.fromWei(balance, 'ether')
    await update.message.reply_text(f"💼 Wallet Address: {acct.address}\nBalance: {eth_balance} tMON")

# Placeholder async command handlers
def buy(update, context): pass
def sell(update, context): pass
def approve(update, context): pass
def snipe(update, context): pass
def chart(update, context): pass
def watch(update, context): pass
def recent(update, context): pass
def gas(update, context): pass
def dexs(update, context): pass
def send(update, context): pass

def price_watcher(app): pass

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_BOT_API_KEY")
    if not TOKEN:
        raise ValueError("Set TELEGRAM_BOT_API_KEY in your environment variables")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("snipe", snipe))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("watch", watch))
    app.add_handler(CommandHandler("recent", recent))
    app.add_handler(CommandHandler("gas", gas))
    app.add_handler(CommandHandler("dexs", dexs))
    app.add_handler(CommandHandler("createwallet", create_wallet))
    app.add_handler(CommandHandler("importwallet", import_wallet))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CallbackQueryHandler(menu_callback))

    print("MonadTrenchBot is running...")
    app.run_polling(asyncio.get_event_loop().create_task(price_watcher(app)))
