import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATA_FILE = "database.json"

CATEGORIES = [
    "Продукты",
    "Кафе",
    "Транспорт",
    "Жильё",
    "Подписки",
    "Развлечения",
    "Покупки",
    "Здоровье",
    "Другое"
]

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "expenses": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Я ilya_budget_bot 🤖\n"
        "Семейный бот для учёта расходов.\n\n"
        "Сначала зарегистрируйся командой:\n"
        "/register"
    )

def register(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    name = update.message.from_user.first_name

    data = load_data()

    if user_id in data["users"]:
        update.message.reply_text("Ты уже зарегистрирован 👍")
        return

    data["users"][user_id] = {"name": name}
    save_data(data)

    update.message.reply_text(
        f"Готово! Ты зарегистрирован как: {name}\n\n"
        "Теперь можешь добавлять расходы в формате:\n"
        "категория сумма\n\n"
        "Пример:\nПродукты 1200"
    )

def add_expense(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    data = load_data()

    if user_id not in data["users"]:
        update.message.reply_text("Сначала зарегистрируйся: /register")
        return

    parts = text.split()

    if len(parts) < 2:
        update.message.reply_text("Формат: категория сумма\nПример: Кафе 500")
        return

    category = parts[0]
    amount = parts[1]

    if category not in CATEGORIES:
        update.message.reply_text(
            "Неизвестная категория.\nДоступные:\n" + ", ".join(CATEGORIES)
        )
        return

    try:
        amount = float(amount)
    except:
        update.message.reply_text("Сумма должна быть числом")
        return

    expense = {
        "user_id": user_id,
        "category": category,
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    data["expenses"].append(expense)
    save_data(data)

    update.message.reply_text(
        f"✅ Добавлено:\nКатегория: {category}\nСумма: {amount} ₽"
    )

def my_report(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    data = load_data()

    total = sum(
        e["amount"] for e in data["expenses"]
        if e["user_id"] == user_id
    )

    update.message.reply_text(
        f"Твои общие расходы: {total} ₽"
    )

def family_report(update: Update, context: CallbackContext):
    data = load_data()
    total = sum(e["amount"] for e in data["expenses"])

    update.message.reply_text(
        f"Общие семейные расходы: {total} ₽"
    )

def stats(update: Update, context: CallbackContext):
    data = load_data()

    result = "Расходы по категориям:\n\n"

    for cat in CATEGORIES:
        total = sum(
            e["amount"] for e in data["expenses"]
            if e["category"] == cat
        )
        result += f"{cat}: {total} ₽\n"

    update.message.reply_text(result)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(CommandHandler("my", my_report))
    dp.add_handler(CommandHandler("family", family_report))
    dp.add_handler(CommandHandler("stats", stats))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_expense))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
