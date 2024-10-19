import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

# Загрузка настроек из config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config['bot_token']
ADMINS = config['admins']
ENCODING = config.get('encoding', 'utf-8')  # Выбор кодировки из config.json, по умолчанию utf-8
TEXTS = config['texts']
BUTTONS = config['buttons']
CHAT_SETTINGS = config['chat_settings']
REVIEW_SETTINGS = config['review_settings']
CATALOG_SETTINGS = config['catalog_settings']
REGISTRATION_SETTINGS = config['registration_settings']

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Простая "база данных" пользователей и товаров
users_db = {}
catalog = []
active_chats = {}


# Убираем перекодирование
def decode_text(text):
    return text


# Функция проверки, зарегистрирован ли пользователь
def is_registered(user_id):
    return str(user_id) in users_db


# Регистрация пользователя
@dp.message_handler(commands=['register'])
async def register_user(message: types.Message):
    if is_registered(message.from_user.id):
        await message.reply(decode_text(TEXTS['registration_success']))
        return

    await message.reply(decode_text(TEXTS['registration_request']))
    dp.register_message_handler(process_registration, state='registration')


async def process_registration(message: types.Message):
    user_info = message.text.split()  # Собираем информацию о пользователе
    if len(user_info) < len(REGISTRATION_SETTINGS['registration_fields']):
        await message.reply("Пожалуйста, введите все необходимые данные.")
        return

    users_db[str(message.from_user.id)] = {
        "username": user_info[0],
        "email": user_info[1],
        "phone_number": user_info[2]
    }
    await message.reply(decode_text(TEXTS['registration_success']))


# Старт и помощь
@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    if REGISTRATION_SETTINGS['require_registration'] and not is_registered(message.from_user.id):
        await register_user(message)
        return

    await message.reply(decode_text(TEXTS['start_message']))


# Показать каталог товаров
@dp.message_handler(commands=['catalog'])
async def show_catalog(message: types.Message):
    if not catalog:
        await message.reply(decode_text(TEXTS['catalog_empty']))
        return

    for i, item in enumerate(catalog[:CATALOG_SETTINGS['max_items_per_page']]):
        keyboard = InlineKeyboardMarkup()
        buy_button = InlineKeyboardButton(decode_text(BUTTONS['buy']), callback_data=f'buy_{item["id"]}')
        keyboard.add(buy_button)

        if CATALOG_SETTINGS['allow_item_editing']:
            edit_button = InlineKeyboardButton(decode_text(BUTTONS['edit_item']), callback_data=f'edit_{item["id"]}')
            keyboard.add(edit_button)

        if CATALOG_SETTINGS['allow_item_deletion']:
            delete_button = InlineKeyboardButton(decode_text(BUTTONS['delete_item']),
                                                 callback_data=f'delete_{item["id"]}')
            keyboard.add(delete_button)

        caption = decode_text(TEXTS['catalog_item_caption']).format(name=item['name'], description=item['description'])
        await message.reply_photo(item['photo'], caption=caption, reply_markup=keyboard)


# Добавление нового товара
@dp.message_handler(commands=['new'])
async def add_new_item(message: types.Message):
    if str(message.from_user.id) not in ADMINS:
        await message.reply(decode_text(TEXTS['no_rights']))
        return

    await message.reply(decode_text(TEXTS['new_item_photo_request']))
    dp.register_message_handler(process_new_item_photo, content_types=['photo'], state='new_item_photo')


async def process_new_item_photo(message: types.Message):
    photo = message.photo[-1].file_id
    await message.reply(decode_text(TEXTS['new_item_name_request']))
    dp.register_message_handler(lambda m: process_new_item_name(m, photo), state='new_item_name')


async def process_new_item_name(message: types.Message, photo):
    name = message.text
    await message.reply(decode_text(TEXTS['new_item_description_request']))
    dp.register_message_handler(lambda m: process_new_item_description(m, name, photo), state='new_item_description')


async def process_new_item_description(message: types.Message, name, photo):
    description = message.text
    new_item = {
        "id": len(catalog) + 1,
        "photo": photo,
        "name": name,
        "description": description,
        "reviews": []
    }
    catalog.append(new_item)
    await message.reply(decode_text(TEXTS['new_item_success']).format(name=name))


# Поиск товара
@dp.message_handler(commands=['search'])
async def search_item(message: types.Message):
    query = message.get_args()
    results = [item for item in catalog if
               query.lower() in item['name'].lower() or query.lower() in item['description'].lower()]

    if not results:
        await message.reply(decode_text(TEXTS['search_query_empty']))
        return

    for item in results:
        keyboard = InlineKeyboardMarkup()
        buy_button = InlineKeyboardButton(decode_text(BUTTONS['buy']), callback_data=f'buy_{item["id"]}')
        keyboard.add(buy_button)
        caption = decode_text(TEXTS['catalog_item_caption']).format(name=item['name'], description=item['description'])
        await message.reply_photo(item['photo'], caption=caption, reply_markup=keyboard)


# Покупка товара и запрос на чат
@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def process_buy_request(callback_query: types.CallbackQuery):
    item_id = int(callback_query.data.split('_')[1])
    item = next((i for i in catalog if i['id'] == item_id), None)

    if item:
        buyer = callback_query.from_user.username
        seller_id = ADMINS[0]  # Предполагаем, что первый админ — продавец
        await bot.send_message(seller_id,
                               decode_text(TEXTS['buy_item_request']).format(username=buyer, name=item['name']))
        await bot.send_message(callback_query.from_user.id, decode_text(TEXTS['buy_request_sent']))


# Закрытие чата
@dp.message_handler(commands=['stop'])
async def stop_chat(message: types.Message):
    if message.from_user.id in active_chats:
        del active_chats[message.from_user.id]
        await message.reply(decode_text(TEXTS['chat_stopped']))
    else:
        await message.reply("Чат не найден.")


# Оставить отзыв после завершения сделки
@dp.callback_query_handler(lambda c: c.data.startswith('sale_complete'))
async def sale_complete(callback_query: types.CallbackQuery):
    item_id = int(callback_query.data.split('_')[1])
    item = next((i for i in catalog if i['id'] == item_id), None)

    if item:
        await bot.send_message(callback_query.from_user.id, decode_text(TEXTS['send_review_request']))
        dp.register_message_handler(lambda message: process_review(message, item_id), state='review')


async def process_review(message: types.Message, item_id):
    review = message.text
    item = next((i for i in catalog if i['id'] == item_id), None)

    if item:
        item['reviews'].append(review)
        await message.reply(decode_text(TEXTS['review_received']))
        await bot.send_message(ADMINS[0], decode_text(TEXTS['review_in_catalog']).format(review=review))


# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
