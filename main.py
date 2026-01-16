import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я ilya_budget_bot 🤖\n"
        "Семейный бот для учёта расходов.\n\n"
        "Сначала зарегистрируйся командой:\n"
        "/register"
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    name = update.message.from_user.first_name

    data = load_data()

    if user_id in data["users"]:
        await update.message.reply_text("Ты уже зарегистрирован 👍")
        return

    data["users"][user_id] = {"name": name}
    save_data(data)

    await update.message.reply_text(
        f"Готово! Ты зарегистрирован как: {name}\n\n"
        "Теперь можешь добавлять расходы в формате:\n"
        "категория сумма\n\n"
        "Пример:\nПродукты 1200"
    )


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    data = load_data()

    if user_id not in data["users"]:
        await update.message.reply_text("Сначала зарегистрируйся: /register")
        return

    parts = text.split()

    if len(parts) < 2:
        await update.message.reply_text("Формат: категория сумма\nПример: Кафе 500")
        return

    category = parts[0]
    amount = parts[1]

    if category not in CATEGORIES:
        await update.message.reply_text(
            "Неизвестная категория.\nДоступные:\n" + ", ".join(CATEGORIES)
        )
        return

    try:
        amount = float(amount)
    except:
        await update.message.reply_text("Сумма должна быть числом")
        return

    expense = {
        "user_id": user_id,
        "category": category,
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    data["expenses"].append(expense)
    save_data(data)

    await update.message.reply_text(
        f"✅ Добавлено:\nКатегория: {category}\nСумма: {amount} ₽"
    )


async def my_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_data()

    total = sum(
        e["amount"] for e in data["expenses"]
        if e["user_id"] == user_id
    )

    await update.message.reply_text(
        f"Твои общие расходы: {total} ₽"
    )


async def family_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    total = sum(e["amount"] for e in data["expenses"])

    await update.message.reply_text(
        f"Общие семейные расходы: {total} ₽"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    result = "Расходы по категориям:\n\n"

    for cat in CATEGORIES:
        total = sum(
            e["amount"] for e in data["expenses"]
            if e["category"] == cat
        )
        result += f"{cat}: {total} ₽\n"

    await update.message.reply_text(result)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("my", my_report))
    app.add_handler(CommandHandler("family", family_report))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))

    app.run_polling()


if __name__ == "__main__":
    main()
