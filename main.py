# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import init_db, get_conn
from neighborhoods_loader import NEIGHBORHOODS

# تهيئة البوت والديسباتشر
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==============================
# تعريف الحالات
# ==============================
class ClientStates(StatesGroup):
    subscription_type = State()
    full_name = State()
    phone_number = State()
    city = State()
    neighborhood = State()

class CaptainStates(StatesGroup):
    subscription_type = State()
    full_name = State()
    phone_number = State()
    car_type = State()
    seats = State()
    city = State()
    neighborhoods = State()

# ==============================
# الأزرار الرئيسية
# ==============================
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚗 أنا عميل", callback_data="role_client")],
    [InlineKeyboardButton(text="🛻 أنا كابتن", callback_data="role_captain")]
])

# ==============================
# بدء البوت
# ==============================
@dp.message(commands=["start"])
async def start_handler(message: Message):
    await message.answer("أهلاً بك! اختر دورك:", reply_markup=main_menu)

# ==============================
# اختيار العميل
# ==============================
@dp.callback_query(Text("role_client"))
async def client_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ClientStates.subscription_type)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="يومي", callback_data="sub_daily")],
        [InlineKeyboardButton(text="شهري", callback_data="sub_monthly")]
    ])
    await callback.message.answer("اختر نوع الاشتراك:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(Text(startswith="sub_"))
async def client_subscription(callback: CallbackQuery, state: FSMContext):
    sub_type = "يومي" if callback.data == "sub_daily" else "شهري"
    await state.update_data(subscription_type=sub_type)
    await state.set_state(ClientStates.full_name)
    await callback.message.answer("اكتب اسمك الثلاثي:")
    await callback.answer()

@dp.message(ClientStates.full_name)
async def client_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(ClientStates.phone_number)
    await message.answer("أدخل رقم جوالك:")

@dp.message(ClientStates.phone_number)
async def client_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone_number=phone)
    await state.set_state(ClientStates.city)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 الرياض", callback_data="city_الرياض")],
        [InlineKeyboardButton(text="📍 جدة", callback_data="city_جدة")]
    ])
    await message.answer("اختر مدينتك:", reply_markup=kb)

@dp.callback_query(Text(startswith="city_"))
async def client_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.removeprefix("city_")
    await state.update_data(city=city)
    await state.set_state(ClientStates.neighborhood)

    neighborhoods = NEIGHBORHOODS[city]
    builder = InlineKeyboardBuilder()
    for n in neighborhoods:
        builder.button(text=n, callback_data=f"neigh_{n}")
    builder.adjust(2)

    await callback.message.answer("اختر حيّك:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(Text(startswith="neigh_"))
async def client_neighborhood(callback: CallbackQuery, state: FSMContext):
    neighborhood = callback.data.removeprefix("neigh_")
    data = await state.get_data()

    await state.update_data(neighborhood=neighborhood)

    # حفظ في قاعدة البيانات
    conn = await get_conn()
    await conn.execute("""
        INSERT INTO clients (user_id, subscription_type, full_name, phone_number, city, neighborhood)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (user_id) DO UPDATE
        SET subscription_type=$2, full_name=$3, phone_number=$4, city=$5, neighborhood=$6
    """, callback.from_user.id, data["subscription_type"], data["full_name"], data["phone_number"], data["city"], neighborhood)
    await conn.close()

    await callback.message.answer(f"✅ تم تسجيلك كعميل في {data['city']}، حي {neighborhood}")
    await state.clear()
    await callback.answer()

# ==============================
# اختيار الكابتن
# ==============================
@dp.callback_query(Text("role_captain"))
async def captain_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CaptainStates.subscription_type)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 يومي", callback_data="cap_sub_daily")],
        [InlineKeyboardButton(text="📅 شهري", callback_data="cap_sub_monthly")],
        [InlineKeyboardButton(text="🚗📅 كلاهما", callback_data="cap_sub_both")]
    ])
    await callback.message.answer("اختر نوع الخدمة التي تقدمها:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(Text(startswith="cap_sub_"))
async def captain_subscription(callback: CallbackQuery, state: FSMContext):
    types_map = {
        "cap_sub_daily": "يومي",
        "cap_sub_monthly": "شهري",
        "cap_sub_both": "كلاهما"
    }
    await state.update_data(subscription_type=types_map[callback.data])
    await state.set_state(CaptainStates.full_name)
    await callback.message.answer("اكتب اسمك الثلاثي:")
    await callback.answer()

@dp.message(CaptainStates.full_name)
async def captain_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(CaptainStates.phone_number)
    await message.answer("أدخل رقم جوالك:")

@dp.message(CaptainStates.phone_number)
async def captain_phone(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text.strip())
    await state.set_state(CaptainStates.car_type)
    await message.answer("أدخل نوع سيارتك:")

@dp.message(CaptainStates.car_type)
async def captain_car(message: Message, state: FSMContext):
    await state.update_data(car_type=message.text.strip())
    await state.set_state(CaptainStates.seats)
    await message.answer("كم عدد الركاب الذين تستطيع نقلهم؟")

@dp.message(CaptainStates.seats)
async def captain_seats(message: Message, state: FSMContext):
    await state.update_data(seats=message.text.strip())
    await state.set_state(CaptainStates.city)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 الرياض", callback_data="cap_city_الرياض")],
        [InlineKeyboardButton(text="📍 جدة", callback_data="cap_city_جدة")]
    ])
    await message.answer("اختر مدينتك:", reply_markup=kb)

@dp.callback_query(Text(startswith="cap_city_"))
async def captain_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.removeprefix("cap_city_")
    await state.update_data(city=city)
    await state.set_state(CaptainStates.neighborhoods)

    neighborhoods = NEIGHBORHOODS[city]
    builder = InlineKeyboardBuilder()
    for n in neighborhoods:
        builder.button(text=n, callback_data=f"cap_neigh_{n}")
    builder.adjust(2)

    await callback.message.answer("اختر 3 أحياء تخدمها (بالضغط على الأحياء):", reply_markup=builder.as_markup())
    await callback.answer()

# لتخزين الأحياء المختارة مؤقتاً
captain_selected = {}

@dp.callback_query(Text(startswith="cap_neigh_"))
async def captain_neigh_select(callback: CallbackQuery, state: FSMContext):
    neigh = callback.data.removeprefix("cap_neigh_")
    uid = callback.from_user.id

    if uid not in captain_selected:
        captain_selected[uid] = []

    if neigh not in captain_selected[uid]:
        captain_selected[uid].append(neigh)

    if len(captain_selected[uid]) == 3:
        data = await state.get_data()
        await state.update_data(neighborhoods=captain_selected[uid])

        # حفظ في قاعدة البيانات
        conn = await get_conn()
        await conn.execute("""
            INSERT INTO captains (user_id, subscription_type, full_name, phone_number, car_type, seats, city, neighborhoods)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id) DO UPDATE
            SET subscription_type=$2, full_name=$3, phone_number=$4, car_type=$5, seats=$6, city=$7, neighborhoods=$8
        """, uid, data["subscription_type"], data["full_name"], data["phone_number"], data["car_type"], data["seats"], data["city"], captain_selected[uid])
        await conn.close()

        # محاولة إيجاد عملاء بنفس الأحياء
        conn = await get_conn()
        matches = await conn.fetch("""
            SELECT * FROM clients
            WHERE city = $1 AND neighborhood = ANY($2::text[])
        """, data["city"], captain_selected[uid])
        await conn.close()

        if matches:
            for client in matches:
                # إعلام الكابتن
                await bot.send_message(uid, f"📢 يوجد عميل يبحث عن توصيل في حي {client['neighborhood']}، اسمه: {client['full_name']}")
                # إعلام العميل
                await bot.send_message(client["user_id"], f"🚗 وجدنا كابتن متاح: {data['full_name']} ({data['car_type']})")
        else:
            await bot.send_message(uid, "✅ تم تسجيلك ككابتن، ولا يوجد حالياً عملاء في أحيائك.")

        await state.clear()
        del captain_selected[uid]
    else:
        await callback.answer(f"تم اختيار {neigh} ({len(captain_selected[uid])}/3)")
