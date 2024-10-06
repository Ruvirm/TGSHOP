import logging
import json
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Задайте токен вашего бота здесь
TOKEN = ""  # Замените на ваш токен

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Словарь для хранения товаров
products = {}
# ID администратора (замените на свой ID)
ADMIN_ID = адмистраторы 
banned_users = []  # Список забаненных пользователей

# Состояние чата
user_chat_state = {}  # Пользователь: "active" или "closed"
user_chat_admin = {}  # Пользователь: ID админа


# Загрузка забаненных пользователей из JSON
def load_banned_users():
    global banned_users
    try:
        with open('banned_users.json', 'r') as f:
            content = f.read()
            # Проверка на пустое содержимое
            if content:
                banned_users = json.loads(content)
            else:
                banned_users = []
    except FileNotFoundError:
        banned_users = []
    except json.JSONDecodeError:
        logger.error(
            "Ошибка декодирования JSON, файл может быть поврежден. Инициализация пустого списка забаненных пользователей.")
        banned_users = []


# Сохранение забаненных пользователей в JSON
def save_banned_users():
    with open('banned_users.json', 'w') as f:
        json.dump(banned_users, f)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    greeting_message = f"Привет, {user.mention_html()}! Добро пожаловать в наш магазин. Используйте /help для просмотра доступных команд."
    await update.message.reply_text(greeting_message, reply_markup=ForceReply(selective=True), parse_mode='HTML')


# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = (
        "/start - Приветственное сообщение\n"
        "/help - Список доступных команд\n"
        "/catalog - Показать каталог товаров\n"
        "/new - Добавить новый товар (только для администраторов)\n"
        "/search <название> - Поиск товара по названию\n"
        "/work - Получить данные пользователя\n"
        "/ban <user_id> - Заблокировать пользователя\n"
        "/unban <user_id> - Разблокировать пользователя"
    )
    await update.message.reply_text(commands)


# Показать каталог товаров
async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not products:
        await update.message.reply_text("В магазине пока нет товаров.")
        return

    for name, data in products.items():
        images = data['images']
        description = data['description']
        price = data['price']

        # Создание кнопки "Купить" с указанием цены
        buy_button = InlineKeyboardButton(f"Купить за {price}₽", callback_data=f'buy_{name}')
        reply_markup = InlineKeyboardMarkup([[buy_button]])

        # Отправка информации о товаре
        await update.message.reply_photo(
            photo=images[0],  # Отправляем первое изображение
            caption=f"<b>{name}</b>\n{description}",
            reply_markup=reply_markup,
            parse_mode='HTML'  # Устанавливаем режим разметки
        )


# Команда /new для админа
async def new_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для добавления товаров.")
        return

    await update.message.reply_text("Отправьте первое изображение товара.")
    context.user_data['state'] = "WAITING_FOR_IMAGES"
    context.user_data['images'] = []
    context.user_data['description'] = ''  # Инициализация описания
    context.user_data['title'] = ''  # Инициализация названия


# Обработка изображений
async def handle_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('state') == "WAITING_FOR_IMAGES":
        if update.message.photo:
            images = context.user_data.get('images', [])
            images.append(update.message.photo[-1].file_id)
            context.user_data['images'] = images

            # Предложение добавить еще одно изображение
            if len(images) < 1:  # Проверка, если добавлено менее 1 изображения
                await update.message.reply_text("Изображение добавлено. Отправьте следующее изображение товара.")
            else:
                await update.message.reply_text("Изображение добавлено. Отправьте название товара.")
                context.user_data['state'] = "WAITING_FOR_TITLE"

        return


# Обработка нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Необходимо для подтверждения нажатия кнопки

    if query.data.startswith("buy_"):
        product_name = query.data.split('_')[1]
        await query.message.reply_text(f"Вы купили {product_name}!")

    if query.data.startswith("start_chat_"):
        user_id = int(query.data.split('_')[2])
        user_chat_state[user_id] = "active"
        user_chat_admin[user_id] = query.from_user.id  # Сохраняем ID админа
        await query.message.reply_text("Чат с пользователем открыт. Вы можете писать сообщения пользователю.")


# Обработка названия, описания и цены
async def handle_title_description_and_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('state') == "WAITING_FOR_TITLE":
        title = update.message.text
        context.user_data['title'] = title
        await update.message.reply_text("Теперь введите описание товара.")
        context.user_data['state'] = "WAITING_FOR_DESCRIPTION"
        return

    if context.user_data.get('state') == "WAITING_FOR_DESCRIPTION":
        description = update.message.text
        context.user_data['description'] = description
        await update.message.reply_text("Теперь введите цену товара.")
        context.user_data['state'] = "WAITING_FOR_PRICE"
        return

    if context.user_data.get('state') == "WAITING_FOR_PRICE":
        price = update.message.text
        images = context.user_data.get('images', [])
        title = context.user_data.get('title', '')  # Получаем название
        description = context.user_data.get('description', '')

        # Сохранение товара
        products[title] = {
            'price': price,
            'images': images,
            'description': description,
            'count': 0,  # Количество продаж
            'search_count': 0,  # Количество поисков
            'ratings': []  # Список оценок
        }

        await update.message.reply_text(f"Товар '{title}' добавлен с ценой {price}₽.")
        context.user_data.clear()  # Сброс состояния


# Команда /search
async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        search_query = " ".join(context.args)
        found_products = []

        for name, data in products.items():
            if search_query.lower() in name.lower() or search_query.lower() in data['description'].lower():
                found_products.append(name)
                # Увеличение счетчика поисков для данного товара
                data['search_count'] += 1

        if not found_products:
            await update.message.reply_text("Товары не найдены.")
        else:
            await update.message.reply_text("Найденные товары:")
            for name in found_products:
                data = products[name]
                images = data['images']

                # Создание кнопки "Купить" с указанием цены
                buy_button = InlineKeyboardButton(f"Купить за {data['price']}₽", callback_data=f'buy_{name}')
                reply_markup = InlineKeyboardMarkup([[buy_button]])

                # Отправка информации о товаре
                await update.message.reply_photo(
                    photo=images[0],  # Отправляем первое изображение
                    caption=f"<b>{name}</b>\n{data['description']}",
                    reply_markup=reply_markup,
                    parse_mode='HTML'  # Устанавливаем режим разметки
                )
    else:
        await update.message.reply_text("Укажите название товара для поиска.")


# Получить данные пользователя и начать чат
async def work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in banned_users:
        await update.message.reply_text("Вы забанены.")
        return

    # Информация о пользователе
    user_info = f"ID: {user_id}\nИмя: {update.effective_user.first_name}\nФамилия: {update.effective_user.last_name}\nПользователь: @{update.effective_user.username}"

    # Кнопка для начала чата с администратором
    keyboard = [[InlineKeyboardButton("Начать чат", callback_data=f"start_chat_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Новый пользователь хочет начать чат:\n{user_info}",
                                   reply_markup=reply_markup)


# Блокировка пользователя
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id not in banned_users:
            banned_users.append(user_id)
            save_banned_users()
            await update.message.reply_text(f"Пользователь {user_id} заблокирован.")
        else:
            await update.message.reply_text("Пользователь уже заблокирован.")
    else:
        await update.message.reply_text("Использование: /ban <user_id>")


# Разблокировка пользователя
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in banned_users:
            banned_users.remove(user_id)
            save_banned_users()
            await update.message.reply_text(f"Пользователь {user_id} разблокирован.")
        else:
            await update.message.reply_text("Пользователь не был заблокирован.")
    else:
        await update.message.reply_text("Использование: /unban <user_id>")


# Обработка новых сообщений
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in banned_users:
        await update.message.reply_text("Вы забанены.")
        return

    # Пересылаем сообщение админу, если чат активен
    if user_id in user_chat_state and user_chat_state[user_id] == "active":
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"Сообщение от пользователя {user_id}: {update.message.text}")

        # Если это админ отвечает, переслать его сообщение пользователю
        if update.effective_user.id == ADMIN_ID:
            if user_id in user_chat_admin.values():
                await context.bot.send_message(chat_id=user_id,
                                               text=f"Сообщение от администратора: {update.message.text}")


# Команда /stop для остановки чата
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_chat_state:
        del user_chat_state[user_id]
        await update.message.reply_text("Чат закрыт. Вы можете снова отправлять сообщения.")


# Основная функция
def main() -> None:
    load_banned_users()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("catalog", catalog))
    app.add_handler(CommandHandler("new", new_product))
    app.add_handler(CommandHandler("search", search_product))
    app.add_handler(CommandHandler("work", work))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("stop", stop_chat))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(MessageHandler(filters.PHOTO, handle_images))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == '__main__':
    main()
