import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("MATCHING_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "12345678"))


@dataclass
class Blogger:
    id: int
    username: str
    platform: str
    followers: int
    city: str
    niche: str
    contact: str
    engagement_rate: float = 0.0
    status: str = "active"
    notes: str = ""
    last_post: str = ""


@dataclass
class Seller:
    id: int
    telegram_id: int
    name: str
    marketplace: str
    niche: str
    product_name: str
    article: str
    price: float = 0.0
    status: str = "active"
    needs: int = 10


@dataclass
class Match:
    blogger_id: int
    seller_id: int
    status: str = "pending"
    created_at: str = ""


bloggers_db: List[Blogger] = []
sellers_db: List[Seller] = []
matches_db: List[Match] = []


class SellerFSM(StatesGroup):
    waiting_name = State()
    waiting_marketplace = State()
    waiting_niche = State()
    waiting_product = State()
    waiting_article = State()
    waiting_price = State()
    waiting_needs = State()


class BloggerFSM(StatesGroup):
    waiting_platform = State()
    waiting_followers = State()
    waiting_city = State()
    waiting_niche = State()
    waiting_contact = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Я селлер")],
        [KeyboardButton(text="📱 Я блогер")],
        [KeyboardButton(text="⚙️ Админ")],
    ],
    resize_keyboard=True,
)

admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📋 Селлеры", callback_data="list_sellers")],
        [InlineKeyboardButton(text="📋 Блогеры", callback_data="list_bloggers")],
        [InlineKeyboardButton(text="🤝 Мэтчи", callback_data="list_matches")],
    ]
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для бартерного сотрудничества.\n\n"
        "🛒 <b>Селлер</b> — найди микроблогеров для товара\n"
        "📱 <b>Блогер</b> — получай товары бесплатно\n\n"
        "Выбери роль:",
        reply_markup=main_kb,
        parse_mode="HTML",
    )


@router.message(F.text == "🛒 Я селлер")
async def seller_start(message: Message, state: FSMContext):
    await state.set_state(SellerFSM.waiting_name)
    await message.answer("Как к тебе обращаться? (имя или бренд)")


@router.message(SellerFSM.waiting_name)
async def seller_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SellerFSM.waiting_marketplace)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Wildberries")],
            [KeyboardButton(text="OZON")],
            [KeyboardButton(text="Яндекс Маркет")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("На каком маркетплейсе продаёшь?", reply_markup=kb)


@router.message(SellerFSM.waiting_marketplace)
async def seller_marketplace(message: Message, state: FSMContext):
    await state.update_data(marketplace=message.text)
    await state.set_state(SellerFSM.waiting_niche)
    await message.answer("Ниша товара? (beauty, home, lifestyle, mom, другое)")


@router.message(SellerFSM.waiting_niche)
async def seller_niche(message: Message, state: FSMContext):
    await state.update_data(niche=message.text.lower())
    await state.set_state(SellerFSM.waiting_product)
    await message.answer("Название товара?")


@router.message(SellerFSM.waiting_product)
async def seller_product(message: Message, state: FSMContext):
    await state.update_data(product=message.text)
    await state.set_state(SellerFSM.waiting_article)
    await message.answer("Артикул на маркетплейсе?")


@router.message(SellerFSM.waiting_article)
async def seller_article(message: Message, state: FSMContext):
    await state.update_data(article=message.text)
    await state.set_state(SellerFSM.waiting_price)
    await message.answer("Себестоимость товара (₽)? Цифрами.")


@router.message(SellerFSM.waiting_price)
async def seller_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("Введи цену цифрами, например: 450")
        return
    await state.update_data(price=price)
    await state.set_state(SellerFSM.waiting_needs)
    await message.answer("Сколько блогеров нужно? (1–50)")


@router.message(SellerFSM.waiting_needs)
async def seller_needs(message: Message, state: FSMContext):
    try:
        needs = int(message.text)
    except ValueError:
        await message.answer("Введи число, например: 10")
        return
    data = await state.get_data()
    await state.clear()

    seller = Seller(
        id=len(sellers_db) + 1,
        telegram_id=message.from_user.id,
        name=data["name"],
        marketplace=data["marketplace"],
        niche=data["niche"],
        product_name=data["product"],
        article=data["article"],
        price=data["price"],
        needs=needs,
    )
    sellers_db.append(seller)

    matched = [b for b in bloggers_db if b.niche == seller.niche and b.status == "active"][:needs]

    lines = [
        f"✅ <b>Заявка создана!</b>\n",
        f"🛒 {seller.name}",
        f"📦 {seller.product_name}",
        f"🏪 {seller.marketplace} | Артикул: {seller.article}",
        f"💰 Себестоимость: {seller.price}₽",
        f"📊 Нужно блогеров: {seller.needs}",
        f"\n🤝 <b>Подобрано: {len(matched)}</b>",
    ]

    for b in matched:
        lines.append(
            f"\n@{b.username} | {b.platform} | {b.followers} подписчиков | {b.city} | ER {b.engagement_rate}%"
        )
        matches_db.append(
            Match(blogger_id=b.id, seller_id=seller.id, created_at=datetime.now().isoformat())
        )

    if not matched:
        lines.append("\n⚠️ Пока нет подходящих блогеров. Пришлём контакты, как появятся.")

    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=main_kb)


@router.message(F.text == "📱 Я блогер")
async def blogger_start(message: Message, state: FSMContext):
    await state.set_state(BloggerFSM.waiting_platform)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Instagram")],
            [KeyboardButton(text="TikTok")],
            [KeyboardButton(text="Telegram")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Где ведёшь блог?", reply_markup=kb)


@router.message(BloggerFSM.waiting_platform)
async def blogger_platform(message: Message, state: FSMContext):
    await state.update_data(platform=message.text)
    await state.set_state(BloggerFSM.waiting_followers)
    await message.answer("Сколько подписчиков? (пример: 4500)")


@router.message(BloggerFSM.waiting_followers)
async def blogger_followers(message: Message, state: FSMContext):
    try:
        followers = int(message.text)
    except ValueError:
        await message.answer("Введи число, например: 4500")
        return
    await state.update_data(followers=followers)
    await state.set_state(BloggerFSM.waiting_city)
    await message.answer("В каком городе?")


@router.message(BloggerFSM.waiting_city)
async def blogger_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(BloggerFSM.waiting_niche)
    await message.answer("Твоя ниша? (beauty, home, lifestyle, mom, другое)")


@router.message(BloggerFSM.waiting_niche)
async def blogger_niche(message: Message, state: FSMContext):
    await state.update_data(niche=message.text.lower())
    await state.set_state(BloggerFSM.waiting_contact)
    await message.answer("Ссылка на профиль или контакт?")


@router.message(BloggerFSM.waiting_contact)
async def blogger_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    blogger = Blogger(
        id=len(bloggers_db) + 1,
        username=message.from_user.username or f"user_{message.from_user.id}",
        platform=data["platform"],
        followers=data["followers"],
        city=data["city"],
        niche=data["niche"],
        contact=message.text,
        last_post=datetime.now().isoformat(),
    )
    bloggers_db.append(blogger)

    await message.answer(
        f"✅ <b>Ты в базе!</b>\n\n"
        f"📱 {blogger.platform}\n"
        f"👥 {blogger.followers} подписчиков\n"
        f"📍 {blogger.city}\n"
        f"🏷 {blogger.niche}\n\n"
        f"Когда появится селлер с товаром в твоей нише — пришлю уведомление.",
        parse_mode="HTML",
        reply_markup=main_kb,
    )


@router.message(F.text == "⚙️ Админ")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Только для администратора.")
        return
    await message.answer(
        f"📊 <b>Админ-панель</b>\n\n"
        f"Селлеров: {len(sellers_db)}\n"
        f"Блогеров: {len(bloggers_db)}\n"
        f"Мэтчей: {len(matches_db)}\n",
        parse_mode="HTML",
        reply_markup=admin_kb,
    )


@router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    pending = len([m for m in matches_db if m.status == "pending"])
    done = len([m for m in matches_db if m.status == "done"])
    await callback.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"Селлеров: {len(sellers_db)}\n"
        f"Блогеров: {len(bloggers_db)}\n"
        f"Мэтчей: {len(matches_db)}\n"
        f"В ожидании: {pending}\n"
        f"Выполнено: {done}",
        parse_mode="HTML",
        reply_markup=admin_kb,
    )


@router.callback_query(F.data == "list_sellers")
async def list_sellers_callback(callback: CallbackQuery):
    if not sellers_db:
        await callback.answer("Нет селлеров")
        return
    text = "📋 <b>Селлеры:</b>\n\n" + "\n".join(
        f"{s.id}. {s.name} | {s.product_name} | {s.marketplace} | нужно: {s.needs}"
        for s in sellers_db[-10:]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_kb)


@router.callback_query(F.data == "list_bloggers")
async def list_bloggers_callback(callback: CallbackQuery):
    if not bloggers_db:
        await callback.answer("Нет блогеров")
        return
    text = "📋 <b>Блогеры:</b>\n\n" + "\n".join(
        f"{b.id}. @{b.username} | {b.platform} | {b.followers} | {b.niche} | {b.city}"
        for b in bloggers_db[-10:]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_kb)


@router.callback_query(F.data == "list_matches")
async def list_matches_callback(callback: CallbackQuery):
    if not matches_db:
        await callback.answer("Нет мэтчей")
        return
    text = "🤝 <b>Мэтчи:</b>\n\n" + "\n".join(
        f"{m.blogger_id} ↔ {m.seller_id} | {m.status} | {m.created_at[:10]}"
        for m in matches_db[-10:]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_kb)


@router.message(Command("export"))
async def cmd_export(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    data = {
        "bloggers": [asdict(b) for b in bloggers_db],
        "sellers": [asdict(s) for s in sellers_db],
        "matches": [asdict(m) for m in matches_db],
    }
    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    await message.answer_document(document=open(filename, "rb"), caption="📦 Экспорт базы")


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
