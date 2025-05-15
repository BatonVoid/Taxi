import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, BigInteger, select
import logging
from aiogram.client.bot import DefaultBotProperties



default_bot_properties = DefaultBotProperties(parse_mode="HTML")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ==== 🔐 Конфигурация ====
BOT_TOKEN = "7310545401:AAGh7-4WwpQek-fkVsEs6vjWKBfIirlQ-ZE"
REQUIRED_CHANNEL = "@taxi_nukus_tashkent"
ADMIN_ID = 5111968766  # Admin IDs
DATABASE_URL = "sqlite+aiosqlite:///./taxi_bot.db"

# ==== 🧱 База данных ====
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
START_TEXT = """

➤ TAKSI-BOT | NÓKIS - TASHKENT.

Sálem, jolawshı!

Bul bot - Siziń isenimli joldasıńız Tashkent hám Nókis arasındaǵı saparlar ushın.
Tek ǵana bir túyme - hám sizge múnásip avtomobil tabıladı.

Birinshi qaysı jóneliske barmaqshısız?

Sizge qajet bolǵanda, biz sizge kómek beremiz.

✅ Marshrut tańlasańız boldı, qalǵanı menen biz shuǵıllanamız.

✅ 24/7 isleydi.
✅ Ápiwayı. Tez. Isenimli.
"""

TEXT_TASHKENT_NOKIS = """
✅ Tashkentten Nókiske jol almaqshısız.

Biz benen nomer arqalı baylanısıń

➤ <b>Nokisten → Tashkentke</b>
- Jol uzınlıǵı: 1 118 km.
- Waqit <i>15 saat</i>;

➤ <b>Telefon</b>: +998990247517
✅ <b>Qosımsha xızmetler</b>: Amanat bolsa ALÍP KETEMIZ.

Jolıńız bolsın!
"""

TEXT_NOKIS_TASHKENT = """
✅ Nókisten Tashkentke jol almaqshısız.

Biz benen nomer arqalı baylanısıń

➤ <b>Nokisten → Tashkentke</b>
- Jol uzınlıǵı: 1 118 km.
- Waqit <i>15 saat</i>;

➤ <b>Telefon</b>: +998990247517
✅ <b>Qosımsha xızmetler</b>: Amanat bolsa ALÍP KETEMIZ.

Jolıńız bolsın!
"""
class UserStats(Base):
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, index=True)
    interactions = Column(Integer, default=1)

# ==== 🎛 Клавиатуры ====
def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏙 Tashkent → Nókis")],
            [KeyboardButton(text="🌆 Nókis → Tashkent")]
        ],
        resize_keyboard=True
    )

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏙 Tashkent → Nókis")],
            [KeyboardButton(text="🌆 Nókis → Tashkent")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="Xabarlandırıw")]
        ],
        resize_keyboard=True
    )

# ==== 🤖 Логика ====
router = Router()

async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def add_or_update_user(user_id: int):
    async with SessionLocal() as session:
        result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.interactions += 1
        else:
            user = UserStats(user_id=user_id)
            session.add(user)

        await session.commit()

async def broadcast_to_all_users(bot: Bot, text: str):
    async with SessionLocal() as session:
        result = await session.execute(select(UserStats.user_id))
        user_ids = [row[0] for row in result.fetchall()]

    success = 0
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            success += 1
        except Exception:
            pass
    return success

# ==== 🎯 Хендлеры ====

@router.message(CommandStart())
async def cmd_start(message: Message):
    bot = message.bot
    user_id = message.from_user.id

    if not await check_subscription(bot, user_id):
        await message.answer("❗ Dáslep kanalǵa aǵza bolıń: @taxi_nukus_tashkent")
        return

    await add_or_update_user(user_id)

    keyboard = get_admin_keyboard() if user_id == ADMIN_ID else get_user_keyboard()

    await message.answer(
        "Sálemetsiz be! Qay jóneliske taksi kerek?" + START_TEXT,
        reply_markup=keyboard
    )

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with SessionLocal() as session:
        result = await session.execute(select(UserStats))
        users = result.scalars().all()

    total_users = len(users)
    total_interactions = sum(u.interactions for u in users)

    await message.answer(
        f"📈 Жалпы қолданушылар: <b>{total_users}</b>\n"
        f"📊 Жалпы әрекеттер: <b>{total_interactions}</b>",

    )

@router.message(F.text == "Xabarlandırıw")
async def notify_info(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("✍️ Jiberginiz kelgen xabardı jazıń, onı hámme kóredi..")

@router.message(F.text)
async def message_handler(message: Message):
    user_id = message.from_user.id
    text = message.text


    if user_id == ADMIN_ID and text not in ["📊 Statistika", "Xabarlandırıw", "🏙 Tashkent → Nókis", "🌆 Nókis → Tashkent"]:
        count = await broadcast_to_all_users(message.bot, f"📢 Admin xabarı:\n\n{text}")
        await message.answer(f"✅ Xabar {count} adamǵa jiberildi.")
        return

    if text in "🏙 Tashkent → Nókis":
        await add_or_update_user(user_id)
        await message.answer(f"✅ " + TEXT_TASHKENT_NOKIS)


    if text in "🌆 Nókis → Tashkent":
        await add_or_update_user(user_id)
        await message.answer(f"✅ " + TEXT_NOKIS_TASHKENT)


async def main():

    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logging.error(f"Ошибка при создании таблиц: {e}")

    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
