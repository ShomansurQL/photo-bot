import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import create_start_link, decode_payload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))  # Sizning Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart(deep_link=True))
async def start_with_link(message: Message):
    """Kimdir link orqali kelganda"""
    payload = decode_payload(message.text.split(" ")[1] if " " in message.text else "")
    
    user = message.from_user
    user_info = f"👤 <b>Ism:</b> {user.full_name}"
    if user.username:
        user_info += f"\n🔗 <b>Username:</b> @{user.username}"
    user_info += f"\n🆔 <b>ID:</b> <code>{user.id}</code>"
    
    await message.answer(
        "📸 <b>Salom!</b>\n\n"
        "Menga rasm yuboring, men uni egasiga yetkazaman.\n\n"
        f"<i>Payload: {payload}</i>" if payload else
        "📸 <b>Salom!</b>\n\n"
        "Menga rasm yuboring, men uni egasiga yetkazaman.",
        parse_mode="HTML"
    )
    
    # Egasiga xabar yuborish - kimdir link orqali kelgani haqida
    await bot.send_message(
        OWNER_ID,
        f"🔔 <b>Yangi foydalanuvchi link orqali keldi!</b>\n\n{user_info}",
        parse_mode="HTML"
    )


@dp.message(CommandStart())
async def start(message: Message):
    """Oddiy /start"""
    await message.answer(
        "👋 <b>Salom!</b>\n\n"
        "Bu bot orqali menga rasm yuborishingiz mumkin.\n\n"
        "📸 Faqat rasm yuboring!",
        parse_mode="HTML"
    )


@dp.message(Command("link"))
async def generate_link(message: Message):
    """Egasi uchun link generatsiya"""
    if message.from_user.id != OWNER_ID:
        await message.answer("❌ Sizda bu buyruq uchun ruxsat yo'q.")
        return
    
    # Unique link yaratish
    link = await create_start_link(bot, "photo_request", encode=True)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Linkni ochish", url=link)]
    ])
    
    await message.answer(
        f"✅ <b>Sizning link:</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"📤 Bu linkni kimgadir yuboring.\n"
        f"Ular rasm yuborsa, sizga keladi!",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@dp.message(F.photo)
async def receive_photo(message: Message):
    """Rasm qabul qilish va egasiga yuborish"""
    user = message.from_user
    
    # Foydalanuvchi ma'lumotlari
    user_info = f"👤 <b>Ism:</b> {user.full_name}"
    if user.username:
        user_info += f"\n🔗 <b>Username:</b> @{user.username}"
    user_info += f"\n🆔 <b>ID:</b> <code>{user.id}</code>"
    
    caption_text = message.caption or ""
    if caption_text:
        user_info += f"\n💬 <b>Izoh:</b> {caption_text}"
    
    # Egasiga rasmni yuborish
    try:
        await bot.send_photo(
            OWNER_ID,
            photo=message.photo[-1].file_id,  # Eng yuqori sifatli rasm
            caption=f"📸 <b>Yangi rasm keldi!</b>\n\n{user_info}",
            parse_mode="HTML"
        )
        
        # Yuboruvchiga tasdiqlash
        await message.answer(
            "✅ <b>Rasm muvaffaqiyatli yuborildi!</b>\n\n"
            "Rahmat! 🙏",
            parse_mode="HTML"
        )
        
        logger.info(f"Photo received from {user.id} (@{user.username})")
        
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")


@dp.message(F.document)
async def receive_document(message: Message):
    """Fayl sifatida yuborilgan rasmni qabul qilish"""
    user = message.from_user
    
    # Faqat rasm fayllarni qabul qilish
    if message.document.mime_type and message.document.mime_type.startswith("image/"):
        user_info = f"👤 <b>Ism:</b> {user.full_name}"
        if user.username:
            user_info += f"\n🔗 <b>Username:</b> @{user.username}"
        user_info += f"\n🆔 <b>ID:</b> <code>{user.id}</code>"
        user_info += f"\n📎 <b>Fayl nomi:</b> {message.document.file_name}"
        
        try:
            await bot.send_document(
                OWNER_ID,
                document=message.document.file_id,
                caption=f"📎 <b>Yangi rasm (fayl) keldi!</b>\n\n{user_info}",
                parse_mode="HTML"
            )
            
            await message.answer(
                "✅ <b>Rasm (fayl) muvaffaqiyatli yuborildi!</b>\n\n"
                "Rahmat! 🙏",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error sending document: {e}")
            await message.answer("❌ Xatolik yuz berdi.")
    else:
        await message.answer("⚠️ Iltimos, faqat rasm yuboring.")


@dp.message()
async def unknown_message(message: Message):
    """Noma'lum xabar"""
    await message.answer(
        "📸 Iltimos, faqat <b>rasm</b> yuboring!\n\n"
        "Boshqa turdagi xabarlar qabul qilinmaydi.",
        parse_mode="HTML"
    )


async def main():
    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
