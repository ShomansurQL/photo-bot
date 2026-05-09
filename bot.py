import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.deep_linking import create_start_link, decode_payload
import json
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
BOT_TOKEN  = os.getenv("BOT_TOKEN")
OWNER_ID   = int(os.getenv("OWNER_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "")   # Masalan: @mening_kanal yoki -1001234567890
PORT       = int(os.getenv("PORT", 8080))
 
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()
 
 
# ══════════════════════════════════════════
#   SIGNAL FORMATLASH
# ══════════════════════════════════════════
def format_signal(data: dict) -> str:
    signal  = data.get("signal", "?")       # BUY yoki SELL
    symbol  = data.get("symbol", "?")
    tf      = data.get("timeframe", "?")
    entry   = float(data.get("entry", 0))
    sl      = float(data.get("sl", 0))
    tp1     = float(data.get("tp1", 0))
    tp2     = float(data.get("tp2", 0))
    gz_low  = float(data.get("gz_low", 0))
    gz_high = float(data.get("gz_high", 0))
 
    emoji  = "🟢" if signal == "BUY"  else "🔴"
    arrow  = "📈" if signal == "BUY"  else "📉"
    action = "BUY"  if signal == "BUY" else "SELL"
 
    # Pip hisobi
    pip_sl  = abs(entry - sl)
    pip_tp1 = abs(tp1 - entry)
    pip_tp2 = abs(tp2 - entry)
    rr1     = round(pip_tp1 / pip_sl, 1) if pip_sl > 0 else 0
    rr2     = round(pip_tp2 / pip_sl, 1) if pip_sl > 0 else 0
 
    msg  = f"{emoji} <b>{action} {symbol}</b> — {tf}\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"📍 <b>Entry:</b>  <code>{entry:.5f}</code>\n"
    msg += f"🛑 <b>SL:</b>     <code>{sl:.5f}</code>\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🎯 <b>TP1</b> (161.8%): <code>{tp1:.5f}</code>\n"
    msg += f"   ↳ RR: 1:{rr1} | Ehtimol: <b>70%</b> ✅\n"
    msg += f"🎯 <b>TP2</b> (261.8%): <code>{tp2:.5f}</code>\n"
    msg += f"   ↳ RR: 1:{rr2} | Ehtimol: <b>100%</b> 🏆\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🟡 <b>Golden Zone:</b> {gz_low:.5f} — {gz_high:.5f}\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"⚡ <i>Fib Golden Zone strategiyasi</i>\n"
    msg += f"⚠️ <i>Risk menejmentni unutmang!</i>"
 
    return msg
 
 
# ══════════════════════════════════════════
#   WEBHOOK QABUL QILISH (MT5 dan keladi)
# ══════════════════════════════════════════
async def handle_signal(request: web.Request):
    try:
        data = await request.json()
        logger.info(f"Signal keldi: {data}")
 
        msg = format_signal(data)
 
        # Kanalga yuborish
        if CHANNEL_ID:
            await bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
            logger.info(f"Kanalga yuborildi: {CHANNEL_ID}")
 
        # Egasiga ham yuborish
        await bot.send_message(OWNER_ID, msg, parse_mode="HTML")
 
        return web.Response(text="OK", status=200)
 
    except Exception as e:
        logger.error(f"Signal xato: {e}")
        return web.Response(text=str(e), status=500)
 
 
async def handle_health(request: web.Request):
    return web.Response(text="Bot ishlayapti ✅", status=200)
 
 
# ══════════════════════════════════════════
#   BOT BUYRUQLARI
# ══════════════════════════════════════════
@dp.message(CommandStart(deep_link=True))
async def start_with_link(message: Message):
    user = message.from_user
    user_info = f"👤 <b>Ism:</b> {user.full_name}"
    if user.username:
        user_info += f"\n🔗 @{user.username}"
    user_info += f"\n🆔 <code>{user.id}</code>"
 
    await message.answer(
        "📸 <b>Salom!</b>\n\nMenga rasm yuboring!",
        parse_mode="HTML"
    )
    await bot.send_message(
        OWNER_ID,
        f"🔔 <b>Yangi foydalanuvchi!</b>\n\n{user_info}",
        parse_mode="HTML"
    )
 
 
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 <b>Salom!</b>\n\nSignal botiga xush kelibsiz!",
        parse_mode="HTML"
    )
 
 
@dp.message(Command("link"))
async def generate_link(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Ruxsat yo'q.")
        return
    link = await create_start_link(bot, "photo_request", encode=True)
    await message.answer(
        f"✅ <b>Sizning link:</b>\n\n<code>{link}</code>\n\n"
        f"Kimgadir tashlang — rasm yuborsa sizga keladi!",
        parse_mode="HTML"
    )
 
 
@dp.message(Command("setchannel"))
async def set_channel(message: Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Ruxsat yo'q.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "ℹ️ Ishlatish: <code>/setchannel @kanal_username</code>\n\n"
            "Yoki: <code>/setchannel -1001234567890</code>",
            parse_mode="HTML"
        )
        return
    channel = parts[1]
    await message.answer(
        f"✅ Kanal: <code>{channel}</code>\n\n"
        f"⚠️ Railway Variables da <b>CHANNEL_ID</b> = <code>{channel}</code> qo'shing!",
        parse_mode="HTML"
    )
 
 
@dp.message(Command("testbot"))
async def test_signal(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    test_data = {
        "signal": "BUY",
        "symbol": "XAUUSD",
        "timeframe": "PERIOD_H1",
        "entry": 2345.50,
        "sl": 2335.00,
        "tp1": 2361.68,
        "tp2": 2384.89,
        "gz_low": 2338.20,
        "gz_high": 2342.80
    }
    msg = format_signal(test_data)
    await message.answer(msg, parse_mode="HTML")
 
 
@dp.message(F.photo)
async def receive_photo(message: Message):
    user = message.from_user
    user_info = f"👤 {user.full_name}"
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f" | ID: {user.id}"
 
    if message.caption:
        user_info += f"\n💬 {message.caption}"
 
    try:
        await bot.send_photo(
            OWNER_ID,
            photo=message.photo[-1].file_id,
            caption=f"📸 Yangi rasm!\n{user_info}",
        )
        await message.answer("✅ Rasm yuborildi! Rahmat 🙏")
    except Exception as e:
        await message.answer("❌ Xatolik yuz berdi.")
 
 
@dp.message()
async def unknown(message: Message):
    await message.answer("📸 Faqat rasm yuboring yoki /link buyrug'ini ishlating.")
 
 
# ══════════════════════════════════════════
#   ISHGA TUSHIRISH
# ══════════════════════════════════════════
async def main():
    # Web server (webhook uchun)
    app = web.Application()
    app.router.add_post("/signal", handle_signal)
    app.router.add_get("/", handle_health)
 
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Web server port {PORT} da ishlamoqda")
 
    # Bot polling
    logger.info("Bot ishga tushdi!")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())
