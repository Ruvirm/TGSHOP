 # Документация Бота магазина Telegram

 ```json
{
  "bot_token": "ВАШ_ТОКЕН",
  "admins": ["ID АДМИНА"],
  "chat_settings": {
    "allow_chat_between_users": true,
    "chat_auto_close_timeout": 60,  // Время в минутах, после которого чат автоматически закрывается
    "send_notifications": true,  // Отправлять уведомления администраторам при покупках
    "max_concurrent_chats": 5  // Максимальное количество активных чатов с одним продавцом
  },
  "review_settings": {
    "allow_reviews": true,  // Включение системы отзывов
    "max_review_length": 500,  // Максимальная длина отзыва
    "min_review_rating": 1,  // Минимальная оценка
    "max_review_rating": 5   // Максимальная оценка
  },
  "catalog_settings": {
    "max_items_per_page": 5,  // Максимальное количество товаров на странице каталога
    "item_expiration_days": 30,  // Через сколько дней товар удаляется из каталога
    "allow_item_editing": true,  // Разрешить редактирование товара после добавления
    "allow_item_deletion": true  // Разрешить удаление товара
  },
  "registration_settings": {
    "require_registration": true,  // Требовать регистрацию перед использованием бота
    "registration_fields": ["username", "email", "phone_number"]  // Поля, требуемые при регистрации
  },
  "texts": {
    "start_message": "Добро пожаловать в магазин-бот!",
    "catalog_empty": "Каталог пуст.",
    "catalog_item_caption": "{name}\n{description}",
    "new_item_photo_request": "Отправьте фото товара.",
    "new_item_name_request": "Введите имя товара.",
    "new_item_description_request": "Введите описание товара.",
    "new_item_success": "Товар '{name}' успешно добавлен!",
    "no_rights": "У вас нет прав для добавления товара.",
    "search_query_empty": "Товар не найден.",
    "buy_request_sent": "Запрос отправлен продавцу.",
    "seller_accept_request": "Принять запрос?",
    "chat_opened_buyer": "Продавец принял ваш запрос. Открылся чат для товара '{name}'.",
    "chat_opened_seller": "Чат с покупателем открыт.",
    "buy_item_request": "Пользователь {username} хочет купить '{name}'. Принять запрос?",
    "chat_stopped": "Чат закрыт.",
    "sale_completed": "Сделка завершена. Пожалуйста, оставьте отзыв о товаре '{name}'.",
    "send_review_request": "Оставьте ваш отзыв о товаре.",
    "review_received": "Ваш отзыв отправлен!",
    "review_in_catalog": "Отзыв: {review}",
    "registration_request": "Пожалуйста, пройдите регистрацию перед началом работы.",
    "registration_success": "Регистрация прошла успешно!"
  },
  "buttons": {
    "buy": "Купить",
    "accept": "Принять",
    "stop_chat": "Закрыть чат",
    "sale_complete": "Завершить сделку",
    "leave_review": "Оставить отзыв",
    "send_review": "Отправить отзыв",
    "edit_item": "Редактировать товар",
    "delete_item": "Удалить товар",
    "register": "Регистрация"
  }
}
```
