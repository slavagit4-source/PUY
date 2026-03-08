import telebot
from telebot import types
import requests
from datetime import datetime

# Токен бота (получи у @BotFather)
TOKEN = '8706371143:AAEFf8mCWPzzAESMdPt8PHgB9qXDhFZmLmg'

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# API для получения курсов валют
EXCHANGE_API = "https://api.exchangerate-api.com/v4/latest/"

# Доступные валюты
CURRENCIES = {
    'USD': '🇺🇸 Доллар США',
    'EUR': '🇪🇺 Евро',
    'RUB': '🇷🇺 Российский рубль',
    'GBP': '🇬🇧 Фунт стерлингов',
    'JPY': '🇯🇵 Японская йена',
    'CNY': '🇨🇳 Китайский юань',
    'KZT': '🇰🇿 Казахстанский тенге',
    'UAH': '🇺🇦 Украинская гривна',
    'BYN': '🇧🇾 Белорусский рубль',
    'TRY': '🇹🇷 Турецкая лира'
}

# Словарь для хранения временных данных пользователей
user_data = {}

# Функция для получения курса валют
def get_exchange_rate(base_currency, target_currency):
    try:
        response = requests.get(f"{EXCHANGE_API}{base_currency}")
        data = response.json()
        return data['rates'].get(target_currency, None)
    except:
        return None

# Функция для получения всех курсов
def get_all_rates():
    try:
        response = requests.get(f"{EXCHANGE_API}USD")
        data = response.json()
        return data['rates']
    except:
        return None

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    text = f"""👋 Привет, {message.from_user.first_name}!

Я бот для конвертации валют прямо в чате!

📋 Доступные команды:
/convert - Конвертировать валюту
/rates - Показать курсы
/help - Помощь

💱 Поддерживаемые валюты:
{', '.join(CURRENCIES.keys())}"""
    
    bot.send_message(message.chat.id, text)

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    text = """🔍 Как пользоваться ботом:

1️⃣ Конвертация валют:
• Нажми /convert
• Введи сумму
• Выбери валюты из списка

2️⃣ Просмотр курсов:
• Нажми /rates

💱 Доступные валюты:
USD - Доллар США
EUR - Евро
RUB - Российский рубль
GBP - Фунт стерлингов
JPY - Японская йена
CNY - Китайский юань
KZT - Казахстанский тенге
UAH - Украинская гривна
BYN - Белорусский рубль
TRY - Турецкая лира

Пример: 100 USD в EUR"""
    
    bot.send_message(message.chat.id, text)

# Команда /rates
@bot.message_handler(commands=['rates'])
def show_rates(message):
    bot.send_message(message.chat.id, "🔄 Получаю курсы...")
    
    rates_data = get_all_rates()
    
    if rates_data:
        # Создаем сообщение с курсами (без тегов code)
        text = "💱 КУРСЫ ВАЛЮТ К USD\n"
        text += "═════════════════════\n"
        
        # Добавляем каждую валюту
        for code, name in CURRENCIES.items():
            if code in rates_data:
                rate = rates_data[code]
                # Добавляем пробелы для выравнивания
                spaces = " " * (4 - len(code))
                text += f"{code}{spaces} {name[:12]} : {rate:>10.4f}\n"
        
        text += "═════════════════════\n"
        text += f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "❌ Ошибка! Не удалось получить курсы.")

# Команда /convert
@bot.message_handler(commands=['convert'])
def convert_start(message):
    user_id = message.from_user.id
    user_data[user_id] = {'step': 'amount'}
    
    msg = bot.send_message(
        message.chat.id,
        "💰 Конвертация валют\n\nВведите сумму для конвертации:\n(например: 100 или 100.50)"
    )
    bot.register_next_step_handler(msg, process_amount)

# Обработка суммы
def process_amount(message):
    user_id = message.from_user.id
    
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError()
        
        user_data[user_id]['amount'] = amount
        user_data[user_id]['step'] = 'from_currency'
        
        # Создаем клавиатуру с валютами
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        buttons = list(CURRENCIES.keys())
        markup.add(*buttons)
        markup.add(types.KeyboardButton("❌ Отмена"))
        
        bot.send_message(
            message.chat.id,
            f"Сумма: {amount}\n\nВыберите исходную валюту:",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, process_from_currency)
        
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "❌ Ошибка! Введите корректное число:"
        )
        bot.register_next_step_handler(msg, process_amount)

# Обработка исходной валюты
def process_from_currency(message):
    user_id = message.from_user.id
    
    if message.text == "❌ Отмена":
        bot.send_message(
            message.chat.id,
            "✅ Операция отменена",
            reply_markup=types.ReplyKeyboardRemove()
        )
        if user_id in user_data:
            del user_data[user_id]
        return
    
    if message.text not in CURRENCIES:
        msg = bot.send_message(
            message.chat.id,
            "❌ Неверная валюта! Выберите из списка на клавиатуре:"
        )
        bot.register_next_step_handler(msg, process_from_currency)
        return
    
    user_data[user_id]['from_currency'] = message.text
    user_data[user_id]['step'] = 'to_currency'
    
    # Создаем клавиатуру без выбранной валюты
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [code for code in CURRENCIES.keys() if code != message.text]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("❌ Отмена"))
    
    bot.send_message(
        message.chat.id,
        f"Исходная валюта: {message.text}\n\nВыберите целевую валюту:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, process_to_currency)

# Обработка целевой валюты и конвертация
def process_to_currency(message):
    user_id = message.from_user.id
    
    if message.text == "❌ Отмена":
        bot.send_message(
            message.chat.id,
            "✅ Операция отменена",
            reply_markup=types.ReplyKeyboardRemove()
        )
        if user_id in user_data:
            del user_data[user_id]
        return
    
    if message.text not in CURRENCIES:
        msg = bot.send_message(
            message.chat.id,
            "❌ Неверная валюта! Выберите из списка на клавиатуре:"
        )
        bot.register_next_step_handler(msg, process_to_currency)
        return
    
    # Получаем данные
    amount = user_data[user_id]['amount']
    from_curr = user_data[user_id]['from_currency']
    to_curr = message.text
    
    # Получаем курс
    rate = get_exchange_rate(from_curr, to_curr)
    
    if rate:
        result = amount * rate
        
        # Создаем сообщение с результатом (без тегов HTML)
        result_text = f"""✅ РЕЗУЛЬТАТ КОНВЕРТАЦИИ
═════════════════════
💰 {amount:.2f} {from_curr}
↓ по курсу 1:{rate:.4f} ↓
💵 {result:.2f} {to_curr}
═════════════════════
🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}

{CURRENCIES[from_curr]} → {CURRENCIES[to_curr]}"""
        
        bot.send_message(
            message.chat.id,
            result_text,
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Предлагаем новые действия
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔄 Новая конвертация", callback_data="new_convert"),
            types.InlineKeyboardButton("📊 Курсы валют", callback_data="show_rates")
        )
        
        bot.send_message(
            message.chat.id,
            "🔍 Что дальше?",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка получения курса! Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    if user_id in user_data:
        del user_data[user_id]

# Обработка инлайн кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "new_convert":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        convert_start(call.message)
    elif call.data == "show_rates":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_rates(call.message)

# Обработка обычных сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = """🤖 Я понимаю только команды!

Используйте:
/convert - Конвертация
/rates - Курсы валют
/help - Помощь"""
    
    bot.send_message(message.chat.id, text)

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()