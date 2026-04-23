import time, qrcode
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import dns.resolver

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
# -------- CONFIG --------
API_ID = 34039354
API_HASH = "e8f8739959e4fbe917f4780c13625543"
BOT_TOKEN = "8710805840:AAESMNAP0iPBEvHEHvr5LX_nWY4qfATLgW8"
ADMIN_ID = 8094093317

MONGO_URL = "mongodb+srv://Abhinav_x07:Z1j9XF3azcjvbJsr@cluster0.ini1aqt.mongodb.net/mydb?retryWrites=true&w=majority"

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# -------- DB --------
mongo = MongoClient(MONGO_URL)
db = mongo["bot"]
users_db = db["users"]
# -------- MEMORY --------
users = {}
payments = {}
def get_upi():
    data = users_db.find_one({"_id": "upi"})
    return data["value"] if data else "abhinav62@fam"

def set_upi(upi):
    users_db.update_one(
        {"_id": "upi"},
        {"$set": {"value": upi}},
        upsert=True
    )
# -------- PREMIUM --------
def is_premium(uid):
    user = users_db.find_one({"_id": uid})
    return user.get("premium", False) if user else False

def add_user(uid):
    if not users_db.find_one({"_id": uid}):
        users_db.insert_one({"_id": uid, "premium": False})

# -------- MENU --------
def menu(uid):
    kb = [[InlineKeyboardButton("🛒 Shop", "shop")]]

    if is_premium(uid):
        kb.append([InlineKeyboardButton("🔑 Reselling", "resale")])

    kb += [
        [InlineKeyboardButton("📦 My Orders", "orders")],
        [InlineKeyboardButton("👤 Profile", "profile")],
        [InlineKeyboardButton("📞 Support", "support")]
    ]
    return InlineKeyboardMarkup(kb)

# -------- PRICES --------
SHOP = {
    "drip":{"1":100,"3":190,"7":350,"15":650,"30":900},
    "hg":{"10":340,"20":600,"30":850},
    "prime":{"1":90,"3":180,"7":320,"10":370},
    "pato":{"3":290,"7":440,"15":750,"30":1000}
}

RESELL = {
    "drip":{"1":50,"3":80,"7":150,"15":245,"30":380},
    "hg":{"10":80,"20":140,"30":270},
    "br":{"1":49,"7":150,"14":200,"30":350},
    "hax":{"10":550,"20":1100,"30":1600}
}

UPI_ID = "abhinav62@fam"

# -------- START --------
@app.on_message(filters.command("start"))
async def start(c, m):
    user = m.from_user

    # 🔥 SAVE USER
    users_db.update_one(
        {"_id": user.id},
        {
            "$set": {
                "name": user.first_name,
                "username": user.username
            }
        },
        upsert=True
    )

    await m.reply(
f"""💥 Yo {user.mention} Welcome To Abhinav Gaming Store Bot!!

─── WHY CHOOSE US ───
🔥🔑 Genuine Premium Keys
⚡ Instant Auto Delivery
🛡️ Secure UPI Payments
💎 Unbeatable Prices
👊 Real 24/7 Support
━━━━━━━━━━━━━━━━━━━━━━
💰 Let's get you a key!""",
        reply_markup=menu(user.id)
    )

# -------- BACK --------
@app.on_callback_query(filters.regex("back_menu"))
async def back(c,q):
    await q.message.edit("🏠 MENU", reply_markup=menu(q.from_user.id))

# -------- PROFILE --------
@app.on_callback_query(filters.regex("profile"))
async def profile(c,q):
    u = q.from_user
    status = "👑 Premium" if is_premium(u.id) else "👤 Regular"

    await q.message.edit(
f"""👤 YOUR PROFILE

📛Name: {u.first_name}
👤Username: @{u.username if u.username else 'N/A'}
🆔ID: {u.id}
🏷Type: {status}""",
reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ BACK","back_menu")]])
)

# -------- ORDERS --------
@app.on_callback_query(filters.regex("orders"))
async def orders(c,q):
    data = users.get(q.from_user.id)

    if not data:
        return await q.message.edit("No orders",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ BACK","back_menu")]]))

    await q.message.edit(
f"""LAST ORDER

{data['product']} {data['days']}D
₹{data['amount']}""",
reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ BACK","back_menu")]])
)

# -------- SHOP --------
@app.on_callback_query(filters.regex("^shop$"))
async def shop(c,q):
    kb = [
        [InlineKeyboardButton("DRIP CILENT","buy|drip")],
        [InlineKeyboardButton("HG CHEATS","buy|hg")],
        [InlineKeyboardButton("PRIME HOOK","buy|prime")],
        [InlineKeyboardButton("PATO TEAM","buy|pato")],
        [InlineKeyboardButton("⬅ BACK","back_menu")]
    ]
    await q.message.edit("━━━━━━━━━━━━━━━━━━━━\n🛒ABHINAV X STORE — SHOP\n━━━━━━━━━━━━━━━━━━━━\nChoose a product 👇", reply_markup=InlineKeyboardMarkup(kb))

# -------- BUY --------
@app.on_callback_query(filters.regex("buy\\|"))
async def buy(c,q):
    _,p = q.data.split("|")

    kb=[]
    for d,price in SHOP[p].items():
        kb.append([InlineKeyboardButton(f"{d}Days ₹{price}",f"pay|shop|{p}|{d}")])
    kb.append([InlineKeyboardButton("⬅ BACK","shop")])

    await q.message.edit("Choose a plan 👇", reply_markup=InlineKeyboardMarkup(kb))

# -------- RESELL --------
@app.on_callback_query(filters.regex("^resale$"))
async def resale(c,q):
    if not is_premium(q.from_user.id):
        return await q.answer("Premium only", show_alert=True)

    kb=[
        [InlineKeyboardButton("DRIP CILENT RESELL","r|drip")],
        [InlineKeyboardButton("HG CHEATS RESELL","r|hg")],
        [InlineKeyboardButton("BR MODS RESELL","r|br")],
        [InlineKeyboardButton("HAXXER PRO RESELL","r|hax")],
        [InlineKeyboardButton("⬅ BACK","back_menu")]
    ]
    await q.message.edit("━━━━━━━━━━━━━━━━━━━━\n🛒ABHINAV X STORE — SHOP\n━━━━━━━━━━━━━━━━━━━━\nChoose a product 👇", reply_markup=InlineKeyboardMarkup(kb))

# -------- RESELL PLAN --------
@app.on_callback_query(filters.regex("r\\|"))
async def rplan(c,q):
    _,p=q.data.split("|")

    kb=[]
    for d,price in RESELL[p].items():
        kb.append([InlineKeyboardButton(f"{d}Days ₹{price}",f"pay|resell|{p}|{d}")])
    kb.append([InlineKeyboardButton("⬅ BACK","resale")])

    await q.message.edit("Choose a plan 👇", reply_markup=InlineKeyboardMarkup(kb))

# -------- PAYMENT --------
@app.on_callback_query(filters.regex("pay\\|"))
async def pay(c, q):
    _, typ, p, d = q.data.split("|")

    amount = SHOP[p][d] if typ == "shop" else RESELL[p][d]

    upi = get_upi()  # 🔥 FIX

    txn = str(int(time.time() * 1000))

    payments[txn] = {
        "uid": q.from_user.id,
        "product": p,
        "days": d,
        "amount": amount
    }

    link = f"upi://pay?pa={upi}&pn=Store&am={amount}&cu=INR"

    qr = qrcode.make(link)
    bio = BytesIO()
    qr.save(bio, "PNG")
    bio.seek(0)

    await c.send_photo(
        q.from_user.id,
        bio,
        caption=f"💳 Pay ₹{amount}\n🏦 UPI: {upi}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("PAID", f"paid|{txn}")]
        ])
    )
# -------- PAID --------
@app.on_callback_query(filters.regex("paid\\|"))
async def paid(c,q):
    txn=q.data.split("|")[1]
    users[q.from_user.id]=payments[txn]
    users[q.from_user.id]["wait"]=True
    await q.message.reply("Send UPI name")

# -------- UPI NAME --------
@app.on_message(filters.text & ~filters.command([
    "start","givekey","premium","rmpremium","broadcast"
]))
async def handle_upi(c, m):
    uid = m.from_user.id

    if uid not in users or not users[uid].get("wait"):
        return

    data = users[uid]
    data["wait"] = False
    data["upi"] = m.text

    # 🔥 ADMIN MESSAGE
    await c.send_message(
        ADMIN_ID,
f"""💰 NEW PAYMENT

👤 User: {m.from_user.mention}
🆔 ID: {uid}

📦 Product: {data['product']}
📅 Days: {data['days']}
💵 Amount: ₹{data['amount']}

🏦 UPI: {m.text}

👉 Send:
 /givekey {uid} KEY"""
    )

    # ✅ USER MESSAGE (UPDATED)
    await m.reply(
"""✅ Approval Submitted To Admin

⏳ Please wait while we verify your payment.
🔑 Your key will be delivered soon."""
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

# -------- GIVE KEY --------
@app.on_message(filters.command("givekey"))
async def givekey(c,m):
    if m.from_user.id!=ADMIN_ID:
        return

    try:
        _,uid,key=m.text.split(maxsplit=2)
        await c.send_message(int(uid),f"KEY:\n{key}")
        users.pop(int(uid),None)
        await m.reply(f"Key Was Sended To {uid}")
    except:
        await m.reply("Usage /givekey id key")

# -------- PREMIUM --------
@app.on_message(filters.command("premium"))
async def prem(c,m):
    if m.from_user.id!=ADMIN_ID:
        return

    uid=int(m.text.split()[1])
    users_db.update_one({"_id":uid},{"$set":{"premium":True}},upsert=True)
    await m.reply(f"Premium Added To {uid}")

# -------- REMOVE PREMIUM --------
@app.on_message(filters.command("rmpremium"))
async def rmp(c,m):
    if m.from_user.id!=ADMIN_ID:
        return

    uid=int(m.text.split()[1])
    users_db.update_one({"_id":uid},{"$set":{"premium":False}})
    await m.reply(f"Premium Removed Form {uid}")

# -------- BROADCAST --------
@app.on_message(filters.command("broadcast"))
async def broadcast(c, m):
    if m.from_user.id != ADMIN_ID:
        return

    if not m.reply_to_message:
        return await m.reply("Reply to message")

    msg = m.reply_to_message

    users = users_db.find()

    sent = 0
    failed = 0

    for user in users:
        try:
            await msg.copy(user["_id"])
            sent += 1
        except:
            failed += 1

    await m.reply(f"✅ Sent: {sent}\n❌ Failed: {failed}")
    
@app.on_message(filters.command("setupi"))
async def setupi(c, m):
    if m.from_user.id != ADMIN_ID:
        return

    try:
        new_upi = m.text.split()[1]
        set_upi(new_upi)

        await m.reply(f"✅ UPI Updated: {new_upi}")
    except:
        await m.reply("Usage:\n/setupi yourupi@id")
   
app.run()
