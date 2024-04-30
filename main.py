import config
import telebot
import sqlite3
import time
import os
import schedule
from scraping import conversion
from telebot import types

# connect bot API
bot = telebot.TeleBot(config.token)


def update_db():
    db = sqlite3.connect(config.data_base)
    cursor = db.cursor()
    cursor.execute(f"""
                    UPDATE users
                    SET usage = 0
                    """)
    db.commit()
    db.close()


@bot.message_handler(commands=['start'])
def get_phone(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reg_button = types.KeyboardButton(text="Send phone number",
                                      request_contact=True)
    markup.add(reg_button)
    send = bot.send_message(message.chat.id, 'To get started we need to get your phone number 📱', reply_markup=markup)
    bot.register_next_step_handler(send, start)


def start(message):
    # clear all buttons
    markup = types.ReplyKeyboardRemove()
    # adding user data to db
    bot.send_message(message.chat.id,
                     "🌟 Hello! 🌟\n\nThank you for choosing us, the default language is ENG🇺🇸, to change this language please select /change_language.\n\nFor help, click /info and get answers to the most frequently asked questions.❓\n\nTo start converting, click /converting and follow the instructions.\n\nGood luck❤️",
                     reply_markup=markup)
    db = sqlite3.connect(config.data_base)
    cursor = db.cursor()
    names = [i[0] for i in cursor.execute("""SELECT name FROM users""").fetchall()]
    if message.from_user.username not in names:
        cursor.execute(f"""INSERT INTO users (name, id, status, phone_number) VALUES 
           ('{message.from_user.username}', {message.chat.id}, 'default_user', '{message.contact.phone_number}')""")
        db.commit()
        db.close()


# language change
@bot.message_handler(commands=['change_language'])
def change_language(message):
    # keyboard
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("RUS🇷🇺", callback_data="rus")
    btn2 = types.InlineKeyboardButton("ENG🇺🇸", callback_data="eng")
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, "Choose a language", reply_markup=markup)


# user information
@bot.message_handler(commands=['info'])
def info(message):
    db = sqlite3.connect(config.data_base)
    cursor = db.cursor()
    if cursor.execute(f"""SELECT language FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] == "ENG":
        # keyboard
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("What kind of bot is this❓", callback_data="Excelify")
        btn2 = types.InlineKeyboardButton("How to convert❓", callback_data="convert")
        btn3 = types.InlineKeyboardButton("Are there any restrictions❓", callback_data="restrictions")
        btn4 = types.InlineKeyboardButton("What is the future of the project❓", callback_data="future")
        markup.add(btn1, btn2, btn3, btn4)

        bot.send_message(message.chat.id,
                         "🌟 Great! 🌟\nHere you can get answers to the most frequently asked questions and find a description of each bot command.\n\nCommands for the bot:\n\n/start - Starts the bot, the very first command the user presses.\n/converting - A command that starts the process of converting a PDF file to XLSX table format\n/change_language - Allows you to change the language\n/info - The menu you are currently in provides assistance for the user in communicating with the bot\n\n❗️Here are some of the most frequently asked questions and their answers❗️",
                         reply_markup=markup)
    else:
        # keyboard
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Что это за бот❓", callback_data="Excelify")
        btn2 = types.InlineKeyboardButton("Как конвертировать❓", callback_data="convert")
        btn3 = types.InlineKeyboardButton("Есть ли какие-либо ограничения❓", callback_data="restrictions")
        btn4 = types.InlineKeyboardButton("Каково будущее проекта❓", callback_data="future")
        markup.add(btn1, btn2, btn3, btn4)

        bot.send_message(message.chat.id,
                         "🌟 Отлично! 🌟\nЗдесь вы можете получить ответы на наиболее часто задаваемые вопросы и найти описание каждой команды бота.\n\nКоманды для бота:\n\n/start — запускает бота, самая первая команда, которую нажимает пользователь.\n/converting — команда, запускающая процесс преобразования файла PDF в формат таблицы XLSX.\n/change_language — позволяет изменить язык.\n/info — меню, в котором вы сейчас находитесь, помогает пользователю общаться с bot\n\n❗️Вот некоторые из наиболее часто задаваемых вопросов и ответы на них❗️",
                         reply_markup=markup)
    db.commit()
    db.close()


@bot.message_handler(commands=['converting'])
def converting(message):
    db = sqlite3.connect(config.data_base)
    cursor = db.cursor()
    if cursor.execute(f"""SELECT usage FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] < 20 or \
            cursor.execute(f"""SELECT status FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] == "admin":
        if cursor.execute(f"""SELECT language FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] == "ENG":
            bot_new_message = bot.send_message(message.chat.id, "Send the file")
            bot.register_next_step_handler(bot_new_message, load)
        else:
            bot_new_message = bot.send_message(message.chat.id, "Отправьте файл")
            bot.register_next_step_handler(bot_new_message, load)
            db.commit()
            db.close()
    else:
        bot.send_message(message.chat.id, "Sorry, but we're done trying for today 💔")


def load(message):
    db = sqlite3.connect(config.data_base)
    cursor = db.cursor()
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = config.file_path + message.document.file_name
    if cursor.execute(f"""SELECT language FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] == "ENG":
        bot.send_message(message.chat.id, "⚠️ Please wait! The document is being converted ⚠️")
    else:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста подождите! Документ конвертируется ⚠️")
    with open(src, 'wb') as new_file:
        # write data to file
        new_file.write(downloaded_file)
    os.rename(src, "files/" + cursor.execute(f"""SELECT name FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] + ".pdf")
    src = config.file_path + cursor.execute(f"""SELECT name FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] + ".pdf"
    zip_file = config.file_path + cursor.execute(f"""SELECT name FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] + ".zip"
    conversion(src, zip_file)
    try:
        bot.send_document(message.chat.id, open(
            config.file_path + cursor.execute(f"""SELECT name FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] + ".zip", 'rb'))
        cursor.execute(f"""
                        UPDATE users
                        SET usage = usage + 1
                        WHERE id = {message.chat.id}""")
    except:
        bot.send_message(message.chat.id, "⚠️ Error ⚠️")
    time.sleep(5)
    os.remove(src)
    os.remove(config.file_path + cursor.execute(f"""SELECT name FROM users WHERE id = {message.chat.id}""").fetchall()[0][0] + ".zip")
    db.commit()
    db.close()


# handling button clicks
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "rus":
            # language selection (rus)
            db = sqlite3.connect(config.data_base)
            cursor = db.cursor()
            cursor.execute(f"""
                            UPDATE users
                            SET language = "RUS"
                            WHERE id = {call.message.chat.id}""")
            db.commit()
            db.close()
            bot.edit_message_text("Успешно! Вы выбрали русский язык", call.message.chat.id, call.message.message_id)
        elif call.data == "eng":
            # language selection (eng)
            db = sqlite3.connect(config.data_base)
            cursor = db.cursor()
            cursor.execute(f"""
                            UPDATE users
                            SET language = "ENG"
                            WHERE id = {call.message.chat.id}""")
            db.commit()
            db.close()
            bot.edit_message_text("Successfully! You have chosen English", call.message.chat.id,
                                  call.message.message_id)

        elif call.data == "convert":
            db = sqlite3.connect(config.data_base)
            cursor = db.cursor()
            if cursor.execute(f"""SELECT language FROM users WHERE id = {call.message.chat.id}""").fetchall()[0][
                0] == "ENG":
                bot.edit_message_text(
                    "To convert you need to follow these steps:\n\n1.Select the /converting command\n2.Send a PDF file to the bot\n3.Wait for conversion and download the output XLSX file\n\nAs you can see, everything is easy and simple. Good luck❤️",
                    call.message.chat.id, call.message.message_id)
            else:
                bot.edit_message_text(
                    "Для конвертации вам необходимо выполнить следующие действия:\n\n1.Выберите команду /converting\n2.Отправьте PDF-файл боту\n3.Дождитесь конвертации и загрузите выходной файл XLSX\n\nКак видите, все легко и просто. Удачи❤️",
                    call.message.chat.id, call.message.message_id)
            db.commit()
            db.close()

        elif call.data == "Excelify":
            db = sqlite3.connect(config.data_base)
            cursor = db.cursor()
            if cursor.execute(f"""SELECT language FROM users WHERE id = {call.message.chat.id}""").fetchall()[0][0] == "RUS":
                bot.edit_message_text(
                    "Привет! 🌟 \nПредставляем вашему вниманию умного помощника в мире документов – бота Excelify для работы с документами в Telegram! \n\nС его помощью конвертация PDF документов в формат XLSX становится легкой как никогда ранее. Просто загрузите свой PDF файл в чат с ботом, и через мгновение получите его в удобном формате Excel! 📑🔁\n\nНаш бот стремится к идеальной точности и скорости выполнения задачи, чтобы вам не пришлось тратить время на рутинные процессы. Разделение данных, форматирование таблиц, сохранение структуры – все это делает наш бот автоматически, помогая вам экономить время и силы для важных дел.\n\nНе упустите шанс упростить свою работу с документами, воспользуйтесь удобным и надежным инструментом – Excelify, для конвертации PDF в XLSX прямо сейчас! 💼✨",
                    call.message.chat.id, call.message.message_id)
            else:
                bot.edit_message_text(
                    "Hello! 🌟 \nWe present to your attention a smart assistant in the world of documents - the Excelify bot for working with documents in Telegram! \n\nWith it, converting PDF documents to XLSX format becomes easier than ever before. Just upload your PDF file to the chat with the bot, and in a moment you will receive it in a convenient Excel format! 📑🔁\n\nOur bot strives for ideal accuracy and speed of task completion, so that you do not have to waste time on routine processes. Dividing data, formatting tables, preserving the structure - our bot does all this automatically, helping you save time and effort for important things.\n\nDon't miss the chance to simplify your work with documents, use a convenient and reliable tool - Excelify, to convert PDF to XLSX right now! 💼✨",
                    call.message.chat.id, call.message.message_id)
            db.commit()
            db.close()
        elif call.data == "restrictions":
            db = sqlite3.connect(config.data_base)
            cursor = db.cursor()
            if cursor.execute(f"""SELECT language FROM users WHERE id = {call.message.chat.id}""").fetchall()[0][
                0] == "ENG":
                bot.edit_message_text(
                    "⚠️ Unfortunately, the bot's resources are limited ⚠️\nAnd to avoid any unforeseen problems, the number of conversion requests has been reduced to 20 per day. \nThanks for understanding❤️",
                    call.message.chat.id, call.message.message_id)
            else:
                bot.edit_message_text(
                    "⚠️ К сожалению, ресурсы бота ограничены ⚠️\nИ во избежание непредвиденных проблем количество запросов на конверсию сокращено до 20 в день. \nСпасибо за понимание❤️",
                    call.message.chat.id, call.message.message_id)
            db.commit()
            db.close()
        elif call.data == "future":
            db = sqlite3.connect(config.data_base)
            cursor = db.cursor()
            if cursor.execute(f"""SELECT language FROM users WHERE id = {call.message.chat.id}""").fetchall()[0][
                0] == "ENG":
                bot.edit_message_text(
                    "What is the future of this project❔\n\nI believe that most tools for working with files should be free.\n\nSo in the future I plan to further develop this project and add new features that I hope will make your work a little easier 🎉❤️",
                    call.message.chat.id, call.message.message_id)
            else:
                bot.edit_message_text(
                    "Каково будущее этого проекта❔\n\nЯ считаю, что большинство инструментов для работы с файлами должны быть бесплатными.\n\nПоэтому в будущем я планирую и дальше развивать этот проект и добавлять новые функции, которые, я надеюсь, сделают вашу работу более комфортной 🎉❤️",
                    call.message.chat.id, call.message.message_id)
            db.commit()
            db.close()


schedule.every().day.at("00:00").do(update_db)

if __name__ == '__main__':
    while True:
        schedule.run_pending()
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(3)
            print(e)
