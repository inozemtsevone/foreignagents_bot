import os
import io
import threading
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

app = Flask('')

# Пример имён иноагентов для зачёркивания — ты потом заменишь на свои
ENEMY_NAMES = ['Иван Иванов', 'Пётр Петров', 'Сергей Сергеев']

def strike_run(run):
    """Добавить зачёркивание для текста run"""
    r = run._element
    strike = OxmlElement('w:strike')
    strike.set(qn('w:val'), 'true')
    r.rPr.append(strike)

def process_docx(file_stream):
    doc = Document(file_stream)
    for para in doc.paragraphs:
        for run in para.runs:
            for name in ENEMY_NAMES:
                if name in run.text:
                    # Заменяем имя зачёркнутым
                    new_text = run.text.replace(name, f"{name}")
                    run.text = new_text
                    strike_run(run)
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Пришли мне .docx файл, я зачеркну имена иноагентов.")

def handle_doc(update: Update, context: CallbackContext):
    file = update.message.document.get_file()
    file_bytes = io.BytesIO()
    file.download(out=file_bytes)
    file_bytes.seek(0)
    processed_file = process_docx(file_bytes)
    update.message.reply_document(document=InputFile(processed_file, filename='processed.docx'))

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def main():
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        print("Ошибка: не задан токен BOT_TOKEN")
        return

    threading.Thread(target=run_web).start()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/vnd.openxmlformats-officedocument.wordprocessingml.document"), handle_doc))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
