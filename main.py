import json
import os
import datetime
import csv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

TOKEN = os.getenv("TOKEN")

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет! Я твой бюджет-бот 💰\n\n"
        "Команды:\n"
        "/add 500 еда – добавить расход\n"
        "/income 1000 зарплата – добавить доход\n"
        "/stat – статистика за месяц\n"
        "/export – выгрузить в таблицу CSV"
    )
    await update.message.reply_text(text)

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    try:
        amount = float(context.args[0])
        category = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Формат: /add 500 еда")
        return

    data = load_data()

    if user_id not in data:
        data[user_id] = []

    data[user_id].append({
        "type": "expense",
        "amount": amount,
        "category": category,
        "date": str(datetime.date.today())
    })

    save_data(data)

    await update.message.reply_text(f"Добавлен расход: {amount} ₽ — {category}")

async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    try:
        amount = float(context.args[0])
        category = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Формат: /income 1000 зарплата")
        return

    data = load_data()

    if user_id not in data:
        data[user_id] = []

    data[user_id].append({
        "type": "income",
        "amount": amount,
        "category": category,
        "date": str(datetime.date.today())
    })

    save_data(data)

    await update.message.reply_text(f"Добавлен доход: {amount} ₽ — {category}")

async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    data = load_data()

    if user_id not in data:
        await update.message.reply_text("У тебя пока нет записей")
        return

    month = datetime.date.today().month

    expenses = sum(
        x["amount"] for x in data[user_id]
        if x["type"] == "expense" and int(x["date"].split("-")[1]) == month
    )

    incomes = sum(
        x["amount"] for x in data[user_id]
        if x["type"] == "income" and int(x["date"].split("-")[1]) == month
    )

    result = (
        f"📊 Статистика за месяц:\n\n"
        f"Доходы: {incomes} ₽\n"
        f"Расходы: {expenses} ₽\n"
        f"Баланс: {incomes - expenses} ₽"
    )

    await update.message.reply_text(result)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    data = load_data()

    if user_id not in data:
        await update.message.reply_text("Нет данных для экспорта")
        return

    filename = f"export_{user_id}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Тип", "Сумма", "Категория", "Дата"])

        for row in data[user_id]:
            writer.writerow([
                row["type"],
                row["amount"],
                row["category"],
                row["date"]
            ])

    await update.message.reply_document(document=open(filename, "rb"))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    parts = text.split()

    if len(parts) >= 2 and parts[0].isdigit():
        amount = parts[0]
        category = " ".join(parts[1:])

        context.args = [amount, category]
        await add_expense(update, context)
    else:
        await update.message.reply_text(
            "Я не понял 😕\n"
            "Попробуй формат: 500 еда"
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_expense))
    app.add_handler(CommandHandler("income", add_income))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("export", export))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
