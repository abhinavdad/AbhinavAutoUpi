import os
import json
import time
import qrcode
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# -------- CONFIG --------
API_ID = 34039354
API_HASH = "e8f8739959e4fbe917f4780c13625543"
BOT_TOKEN = "8710805840:AAESMNAP0iPBEvHEHvr5LX_nWY4qfATLgW8"
ADMIN_ID = 8094093317

app = Client("store_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DB_FILE = "data.json"

# -------- DB --------
def load_db():
    if not os.path.exists(DB_FILE):
        return {"upi": "abhinav62@fam", "premium": []}
    return json.load(open(DB_FILE))

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

db = load_db()

users = {}
PAYMENTS = {}
ALL_USERS = set()

# -------- PREMIUM CHECK --------
def is_premium(uid):
    return uid in db.get("premium", [])

# -------- MENU --------
def main_menu(uid):
    kb = [[InlineKeyboardButton("🛒 Shop", callback_data="shop")]]

    # 🔥 IMPORTANT (AUTO HIDE / SHOW)
    if is_premium(uid):
        kb.append([InlineKeyboardButton("🔑 Reselling", callback_data="resale")])

    kb += [
        [InlineKeyboardButton("📦 My Orders", callback_data="orders")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📞 Support", callback_data="support")]
    ]

    return InlineKeyboardMarkup(kb)

# -------- PRICES --------
SHOP = {
    "drip": {"1":100,"3":200,"7":350,"15":700,"30":950},
    "hg": {"10":340,"20":600,"30":850},
    "prime": {"1":90,"3":180,"7":320,"10":370},
    "br": {"1":90,"7":280,"14":450,"30":800}, 
    "pato": {"3":290,"7":440,"15":750,"30":1000}, 
    "hax": {"10":550,"20":1050,"30":1600}
}

RESELL = {
    "drip": {"1":45,"3":75,"7":145,"15":235,"30":380},
    "hg": {"10":80,"20":140,"30":270},
    "prime": {"1":49,"3":80,"7":150,"10":250},
    "br": {"1":49,"7":150,"14":200,"30":350},
    "hax": {"10":550,"20":1050,"30":1600}
}

# -------- START --------
@app.on_message(filters.command("start"))
async def start(client, message):
    ALL_USERS.add(message.from_user.id)
    mention = message.from_user.mention

    await message.reply(
f"""💥 Yo {mention} Welcome Back To Abhinav Gaming Store Bot!!

─── WHY CHOOSE US ───
🔥🔑 Genuine Premium Keys
⚡ Instant Auto Delivery
🛡️ Secure UPI Payments
💎 Unbeatable Prices
👊 Real 24/7 Support
━━━━━━━━━━━━━━━━━━━━━━
💰 Let's get you a key!""",
        reply_markup=main_menu(message.from_user.id)
    )

# -------- BACK --------
@app.on_callback_query(filters.regex("back_menu"))
async def back_menu(client, query):
    mention = query.from_user.mention
    await query.message.edit(
        f"💥 Yo {mention} Welcome Back!!",
        reply_markup=main_menu(query.from_user.id)
    )

# -------- SHOP --------
@app.on_callback_query(filters.regex("^shop$"))
async def shop(client, query):
    kb = [
        [InlineKeyboardButton("🛒DRIP CILENT", callback_data="buy|drip")],
        [InlineKeyboardButton("🛒HG CHEATS", callback_data="buy|hg")],
        [InlineKeyboardButton("🛒PRIME HOOK ", callback_data="buy|prime")],
        [InlineKeyboardButton("🛒PATO TEAM", callback_data="buy|pato")],
        [InlineKeyboardButton("🛒BR MODS ", callback_data="buy|br")],
        [InlineKeyboardButton("🛒HAXXER PRO", callback_data="buy|hax")],
        [InlineKeyboardButton("⬅ BACK", callback_data="back_menu")]
    ]
    await query.message.edit("🛒 SHOP", reply_markup=InlineKeyboardMarkup(kb))

# -------- SHOP PLAN --------
@app.on_callback_query(filters.regex("^buy\\|"))
async def buy(client, query):
    _, p = query.data.split("|")

    kb = []
    for d, price in SHOP[p].items():
        kb.append([InlineKeyboardButton(f"{d} Days ₹{price}", callback_data=f"pay|shop|{p}|{d}")])

    kb.append([InlineKeyboardButton("⬅ BACK", callback_data="shop")])

    await query.message.edit("📅 Select Plan", reply_markup=InlineKeyboardMarkup(kb))

# -------- RESELL --------
@app.on_callback_query(filters.regex("^resale$"))
async def resale(client, query):
    if not is_premium(query.from_user.id):
        return await query.answer("Premium only", show_alert=True)

    kb = [
        [InlineKeyboardButton("🛒DRIP CILENT", callback_data="r|drip")],
        [InlineKeyboardButton("🛒HG CHEATS", callback_data="r|hg")],
        [InlineKeyboardButton("🛒BR MODS", callback_data="r|br")],
        [InlineKeyboardButton("🛒PRIME HOOK", callback_data="r|prime")],
        [InlineKeyboardButton("🛒HAX PRO", callback_data="r|hax")],
        [InlineKeyboardButton("⬅ BACK", callback_data="back_menu")]
    ]
    await query.message.edit("🔑 RESELL STORE", reply_markup=InlineKeyboardMarkup(kb))

# -------- RESELL PLAN --------
@app.on_callback_query(filters.regex("^r\\|"))
async def rplan(client, query):
    _, p = query.data.split("|")

    kb = []
    for d, price in RESELL[p].items():
        kb.append([InlineKeyboardButton(f"{d} Days ₹{price}", callback_data=f"pay|resell|{p}|{d}")])

    kb.append([InlineKeyboardButton("⬅ BACK", callback_data="resale")])

    await query.message.edit("📦 Select Plan", reply_markup=InlineKeyboardMarkup(kb))

# -------- PAYMENT --------
@app.on_callback_query(filters.regex("^pay\\|"))
async def pay(client, query):
    _, typ, p, d = query.data.split("|")

    amount = SHOP[p][d] if typ == "shop" else RESELL[p][d]
    txn = str(int(time.time()*1000))

    PAYMENTS[txn] = {
        "uid": query.from_user.id,
        "type": typ,
        "product": p,
        "days": d,
        "amount": amount
    }

    upi = db["upi"]
    link = f"upi://pay?pa={upi}&pn=Store&am={amount}&cu=INR&tn={txn}"

    qr = qrcode.make(link)
    bio = BytesIO()
    qr.save(bio, "PNG")
    bio.seek(0)

    await app.send_photo(
        query.from_user.id,
        photo=bio,
        caption=f"💳 Pay ₹{amount}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("PAID", callback_data=f"paid|{txn}")]
        ])
    )

# -------- PAID --------
@app.on_callback_query(filters.regex("^paid\\|"))
async def paid(client, query):
    txn = query.data.split("|")[1]

    users[query.from_user.id] = PAYMENTS[txn]
    users[query.from_user.id]["waiting"] = True

    await query.message.reply("📝 Send your UPI name")

# -------- GET NAME --------
@app.on_message(filters.text & ~filters.command(["start","givekey","premium","rmpremium","setupi"]))
async def get_name(client, message):
    uid = message.from_user.id

    if uid not in users or not users[uid].get("waiting"):
        return

    users[uid]["waiting"] = False

    await message.reply("⏳ Waiting for approval...")

    await app.send_message(
        ADMIN_ID,
        f"""💰 PAYMENT REQUEST

User: {uid}
Type: {users[uid]['type']}
Product: {users[uid]['product']}
Days: {users[uid]['days']}
Amount: ₹{users[uid]['amount']}
UPI Name: {message.text}"""
    )
@app.on_callback_query(filters.regex("^profile$"))
async def profile(client, query):
    u = query.from_user
    status = "👑 Premium" if is_premium(u.id) else "👤 Regular"

    await query.message.edit(
f"""━━━━━━━━━━━━━━━━━━━━
👤 YOUR PROFILE
━━━━━━━━━━━━━━━━━━━━

📛 Name: {u.first_name}
🔗 Username: @{u.username if u.username else 'N/A'}
🆔 User ID: {u.id}
🏷 Account Type: {status}

━━━━━━━━━━━━━━━━━━━━""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅ BACK", callback_data="back_menu")]
        ])
    )

@app.on_callback_query(filters.regex("^orders$"))
async def orders(client, query):
    data = users.get(query.from_user.id)

    if not data:
        return await query.message.edit(
            "📦 No orders found",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ BACK", callback_data="back_menu")]
            ])
        )

    await query.message.edit(
f"""📦 LAST ORDER

Type: {data['type']}
Product: {data['product']}
Days: {data['days']}
Amount: ₹{data['amount']}""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅ BACK", callback_data="back_menu")]
        ])
    )
@app.on_callback_query(filters.regex("support"))
async def support(client, query):
    await query.message.edit(
        "📞 Need help? We're here for you! 🤝\n"
        "📩 Telegram: @Abhinav_x03\n"
        "💡 Include your User ID (from Profile)\n"
        "when contacting for faster help.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅ BACK", callback_data="back_menu")]
        ])
    )
# GIVEKEY
@app.on_message(filters.command("givekey"))
async def givekey(c,m):
    if m.from_user.id!=ADMIN_ID:
        return
    try:
        _,uid,key=m.text.split(maxsplit=2)
        await c.send_message(int(uid),f"KEY:\n{key}")
        users.pop(int(uid),None)
        await m.reply("Done")
    except:
        await m.reply("Usage /givekey id key")
    
# -------- PREMIUM ADD --------
@app.on_message(filters.command("premium"))
async def premium(client, message):
    if message.from_user.id != ADMIN_ID:
        return

    uid = int(message.text.split()[1])

    if uid not in db["premium"]:
        db["premium"].append(uid)
        save_db(db)

    await message.reply("✅ Premium Added")

# -------- PREMIUM REMOVE --------
@app.on_message(filters.command("rmpremium"))
async def remove_premium(client, message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        uid = int(message.text.split()[1])

        if uid in db["premium"]:
            db["premium"].remove(uid)
            save_db(db)
            await message.reply(f"❌ Premium Removed: {uid}")
        else:
            await message.reply("User not premium")

    except:
        await message.reply("Usage: /rmpremium user_id")

# -------- RUN --------
app.run()     
