# Telegram Shop Bot Documentation

## Overview
This bot is designed to manage a shop on Telegram. It allows an admin to add products with images, descriptions, and prices, and customers can browse the catalog, search for products, and make purchases. It also includes a chat feature between the admin and the user, and the admin has the ability to ban users.

---

## Bot Commands
### User Commands:
- **/start** - Displays a welcome message to the user.
- **/help** - Shows a list of available commands.
- **/catalog** - Displays the catalog of products.
- **/search `<name>`** - Searches for a product by name or description.

### Admin Commands:
- **/new** - Starts the process of adding a new product.
- **/work** - Sends the user's information to the admin and initiates the chat system.
- **/stop** - Closes the chat and presents options to ban or accept the user.

---

## Bot Features
1. **Product Management:**
   - Admin can add new products with one image, title, description, and price.
   - Users can browse the catalog and search for specific products.
   - Products in the catalog are displayed with their image, description, and a "Buy" button with the price.

2. **Chat System:**
   - Admin can initiate a chat with a user.
   - During chat mode, all messages from the user are forwarded to the admin and vice versa.
   - Admin can close the chat and choose to either ban or accept the user.

3. **Banning System:**
   - Admin can ban a user after closing the chat.
   - Banned users cannot interact with the bot, and their attempts will return a message: "You are banned."
   - Bans are stored in a JSON file for persistence.

---

## Product Addition Flow

1. **/new** command: 
   - The admin is prompted to upload an image, enter a product title, description, and price.
   - After adding a product, the admin is asked if they want to publish it.
   - Published products become available in the catalog for users to view and purchase.

2. **Catalog Display**:
   - When users call the **/catalog** command, they see all the products with images, titles in **bold**, and a button to buy.

---

## Chat Flow

1. **/work** command:
   - When a user issues this command, the admin receives their details along with a button labeled **Start Chat**.
   - Once the chat is initiated, messages are forwarded between the admin and the user.
   - Admin can close the chat with **/stop**, which presents options to ban, accept, or skip the user.

---

## Example Code

```python
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Replace with your bot's token
TOKEN = "YOUR_BOT_TOKEN"

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Product storage
products = {}
# Banned users storage
banned_users = []
# Admin ID
ADMIN_ID = 5366701738

# Load banned users from JSON
def load_banned_users():
    global banned_users
    try:
        with open('banned_users.json', 'r') as f:
            banned_users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        banned_users = []

# Save banned users to JSON
def save_banned_users():
    global banned_users
    with open('banned_users.json', 'w') as f:
        json.dump(banned_users, f)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id in banned_users:
        await update.message.reply_text("You are banned.")
        return
    greeting_message = f"Hello, {user.first_name}! Welcome to the shop. Use /help to see available commands."
    await update.message.reply_text(greeting_message)

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = (
        "/start - Start the bot\n"
        "/help - List of commands\n"
        "/catalog - View the product catalog\n"
        "/new - Add a new product (admin only)\n"
        "/search <name> - Search for a product\n"
        "/work - Start a chat with the admin"
    )
    await update.message.reply_text(commands)

# Catalog command
async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not products:
        await update.message.reply_text("No products available.")
        return
    for name, data in products.items():
        image = data['image']
        description = data['description']
        price = data['price']
        buy_button = InlineKeyboardButton(f"Buy for {price}₽", callback_data=f'buy_{name}')
        reply_markup = InlineKeyboardMarkup([[buy_button]])
        await update.message.reply_photo(photo=image, caption=f"**{name}**\n{description}", reply_markup=reply_markup)

# Search command
async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        search_query = " ".join(context.args)
        found_products = [name for name, data in products.items() if search_query.lower() in name.lower() or search_query.lower() in data['description'].lower()]
        if not found_products:
            await update.message.reply_text("No products found.")
        else:
            for name in found_products:
                data = products[name]
                image = data['image']
                description = data['description']
                price = data['price']
                buy_button = InlineKeyboardButton(f"Buy for {price}₽", callback_data=f'buy_{name}')
                reply_markup = InlineKeyboardMarkup([[buy_button]])
                await update.message.reply_photo(photo=image, caption=f"**{name}**\n{description}", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Please provide a product name to search.")

# Work command
async def work_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id in banned_users:
        await update.message.reply_text("You are banned.")
        return
    await update.message.reply_text("Your request has been sent to the admin.")
    # Forward user details to the admin
    await context.bot.send_message(ADMIN_ID, f"User {user.first_name} ({user.id}) wants to start a chat. Use /startchat to begin.")

# Chat start command for admin
async def startchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data['chatting_with'] = update.message.reply_to_message.forward_from.id
    await update.message.reply_text("Chat started with the user.")

# Stop chat command
async def stopchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Chat ended. Do you want to ban this user?", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Ban", callback_data='ban'), InlineKeyboardButton("Skip", callback_data='skip')]
    ]))
    del context.user_data['chatting_with']

# Ban user
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = context.user_data.get('chatting_with')
    if user_id:
        banned_users.append(user_id)
        save_banned_users()
        await update.message.reply_text("User banned.")
