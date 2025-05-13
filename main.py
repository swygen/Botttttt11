import logging from aiogram import Bot, Dispatcher, executor, types from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup import requests import os

CONFIGURATION

API_TOKEN = '8177881166:AAGwYtBEJVJR8hzP4siAvNiLK-wOc3Zkxe4' OPENWEATHER_API_KEY = '16970d4b265ce49e2976a76da75fadca' GOOGLE_MAPS_API_KEY = 'AIzaSyBtDCwqkyLa7e-Ayozbx6HGhTruFdH0gMg' GROUP_USERNAME = 'swygenbd'  # Telegram group username without @

Initialize bot and dispatcher

logging.basicConfig(level=logging.INFO) bot = Bot(token=API_TOKEN) dp = Dispatcher(bot)

Language preference storage (in-memory for now)

user_lang = {} user_action = {}

Start command

@dp.message_handler(commands=['start']) async def send_welcome(message: types.Message): user_id = message.from_user.id try: member = await bot.get_chat_member(chat_id=f"@{GROUP_USERNAME}", user_id=user_id) if member.status in ["member", "administrator", "creator"]: await show_language_selection(message) else: await prompt_join_group(message) except: await prompt_join_group(message)

async def prompt_join_group(message: types.Message): join_kb = InlineKeyboardMarkup().add( InlineKeyboardButton("✅ Joined", callback_data="check_join") ) text = ( "বট ব্যবহারের আগে আপনাকে আমাদের অফিসিয়াল গ্রুপে যোগ দিতে হবে: https://t.me/swygenbd\n\nগ্রুপে যোগ দিয়ে নিচের Joined বাটনে ক্লিক করুন।" ) await message.answer(text, parse_mode='Markdown', reply_markup=join_kb)

@dp.callback_query_handler(lambda c: c.data == 'check_join') async def check_joined(callback_query: types.CallbackQuery): user_id = callback_query.from_user.id try: member = await bot.get_chat_member(chat_id=f"@{GROUP_USERNAME}", user_id=user_id) if member.status in ["member", "administrator", "creator"]: await show_language_selection(callback_query.message) else: await prompt_join_group(callback_query.message) except: await prompt_join_group(callback_query.message)

async def show_language_selection(message): lang_kb = InlineKeyboardMarkup(row_width=2) lang_kb.add( InlineKeyboardButton("বাংলা", callback_data='lang_bn'), InlineKeyboardButton("English", callback_data='lang_en') ) user_full_name = message.from_user.full_name welcome_text = f"স্বাগতম, {user_full_name}!\n\nPlease select your language / দয়া করে আপনার ভাষা নির্বাচন করুন:" await message.reply(welcome_text, reply_markup=lang_kb)

Language selection handler

@dp.callback_query_handler(lambda c: c.data.startswith('lang_')) async def set_language(callback_query: types.CallbackQuery): lang = callback_query.data.split('_')[1] user_lang[callback_query.from_user.id] = lang

kb = InlineKeyboardMarkup(row_width=2)
kb.add(
    InlineKeyboardButton("☀️ আবহাওয়া / Weather", callback_data='weather'),
    InlineKeyboardButton("📍 কাছাকাছি সেবা / Nearby", callback_data='nearby'),
    InlineKeyboardButton("🕌 নামাজের সময় / Prayer Times", callback_data='prayer')
)
user_full_name = callback_query.from_user.full_name
welcome_msg = f"স্বাগতম, {user_full_name}! আপনার লোকেশন অনুযায়ী তথ্য পেতে নিচের অপশন থেকে বেছে নিন:" if lang == 'bn' else f"Welcome, {user_full_name}! Choose an option below to get location-based info:"
await bot.send_message(callback_query.from_user.id, welcome_msg, reply_markup=kb)

Callback handler for actions

@dp.callback_query_handler(lambda c: c.data in ['weather', 'nearby', 'prayer']) async def process_callback(callback_query: types.CallbackQuery): action = callback_query.data user_action[callback_query.from_user.id] = action lang = user_lang.get(callback_query.from_user.id, 'en') prompt = "অনুগ্রহ করে 📍 লোকেশন পাঠান, যাতে আমি আপনার জন্য তথ্য খুঁজে দিতে পারি।" if lang == 'bn' else "Please send your 📍 location so I can fetch details for you."

location_btn = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
location_btn.add(KeyboardButton(text="📍 লোকেশন শেয়ার করুন / Share Location", request_location=True))

await bot.send_message(callback_query.from_user.id, prompt, parse_mode='Markdown', reply_markup=location_btn)

Handle location

@dp.message_handler(content_types=types.ContentType.LOCATION) async def handle_location(message: types.Message): user_id = message.from_user.id lang = user_lang.get(user_id, 'en') action = user_action.get(user_id, '') lat = message.location.latitude lon = message.location.longitude

if action == 'weather':
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}&lang={lang}"
    response = requests.get(weather_url).json()
    weather_desc = response['weather'][0]['description'].capitalize()
    temp = response['main']['temp']
    humidity = response['main']['humidity']
    wind_speed = response['wind']['speed']

    text = (
        f"☁️ *আবহাওয়ার তথ্য*\n" if lang == 'bn' else "☁️ *Weather Info*\n"
    ) + (
        f"অবস্থা: {weather_desc}\nতাপমাত্রা: 🌡️ {temp}°C\nআর্দ্রতা: 💧 {humidity}%\nবায়ুর গতি: 🌬️ {wind_speed} m/s"
        if lang == 'bn' else
        f"Condition: {weather_desc}\nTemperature: 🌡️ {temp}°C\nHumidity: 💧 {humidity}%\nWind Speed: 🌬️ {wind_speed} m/s"
    )
    await message.reply(text, parse_mode='Markdown')

elif action == 'nearby':
    place_type = 'restaurant|hospital|pharmacy|atm|store'
    maps_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=1500&type={place_type}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(maps_url).json()
    places = response.get('results', [])

    result_text = "📍 *আপনার কাছাকাছি সেবা সমূহ:*\n\n" if lang == 'bn' else "📍 *Nearby Services:*\n\n"
    if not places:
        sorry = "দুঃখিত, কিছুই পাওয়া যায়নি।" if lang == 'bn' else "Sorry, nothing found near your location."
        await message.reply(sorry, parse_mode='Markdown')
        return

    for place in places[:5]:
        name = place.get('name')
        address = place.get('vicinity')
        rating = place.get('rating', 'N/A')
        result_text += f"🏷️ *{name}*\n📍 {address}\n⭐ রেটিং: {rating}\n\n" if lang == 'bn' else f"🏷️ *{name}*\n📍 {address}\n⭐ Rating: {rating}\n\n"

    await message.reply(result_text, parse_mode='Markdown')

elif action == 'prayer':
    prayer_url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=2"
    response = requests.get(prayer_url).json()
    timings = response['data']['timings']

    if lang == 'bn':
        text = "🕌 *আজকের নামাজের সময়*\n----------------------------\n"
        for name_bn, key in zip(['ফজর', 'সূর্যোদয়', 'যুহর', 'আসর', 'মাগরিব', 'ইশা'], ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']):
            text += f"{name_bn}: {timings[key]}\n"
    else:
        text = "🕌 *Today’s Prayer Times*\n----------------------------\n"
        for name, key in zip(['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'], ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']):
            text += f"{name}: {timings[key]}\n"

    await message.reply(text, parse_mode='Markdown')

Developer credit

@dp.message_handler(commands=['dev']) async def developer_info(message: types.Message): await message.reply("👨‍💻 Developer: Swygen Official ( @Swygen_bd )", parse_mode='Markdown')

Keep-alive handler (useful for render/Heroku)

@dp.message_handler(commands=['ping']) async def ping(message: types.Message): await message.reply("✅ Bot is alive and running!")

if name == 'main': executor.start_polling(dp, skip_updates=True)

