import json
import logging
import os
import re
import time

import requests
#from dotenv import load_dotenv, find_dotenv

import telebot
from telebot import TeleBot

from wiki import Wiki
from geo import Geo
from youtube_pars.parsing import ParsingFromYoutube


#load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")
my_uid = int(os.getenv("my_uid"))

bot = TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help', 'menu', 'geo', 'wiki', 'wiki_list_choose', 'photo_send', 'youtube', 'about_IP'])
def get_text_messages(message: telebot) -> None:
    command = message.text[1:]
    user_id = message.from_user.id
    print(user_id, ':', message.text)
    if user_id != my_uid:
        bot.send_message(my_uid, f"{user_id}: {command}")

    if command == 'start':
        bot.send_message(message.from_user.id, 'Привет! Этот бот может делать разные интересные вещи.')
        bot.send_message(message.from_user.id, 'Возможности бота: /menu')
    elif command == 'menu':
        bot.send_message(message.from_user.id, 'Поиск по гео-координатам - /geo\nВикипедия - /wiki\n'
                                               'Оффлайн плей-лист Youtube - /youtube\nИнформация по IP адресу - /about_IP')
    elif command == 'geo':
        geoloc = Geo(bot, message)
        geoloc.geo()
    elif command == 'wiki':
        wik = Wiki(bot=bot, message=message, lang='ru')
        wik.wiki()
    elif command == 'wiki_list_choose':
        wik = Wiki(bot=bot, message=message, lang='ru', select=False, call_list=True)
        wik.wiki_list(message)
    elif command == 'photo_send':
        # time.sleep(1.5)
        wik = Wiki(bot=bot, message=message, lang='ru', call_photo=True)
        wik.photo_send(message)
    elif command == 'youtube':
        bot.send_message(message.from_user.id, """а) Чтобы получить плей-лист, введите URL.
б) Если желаете получить плей-лист со встроенным видео, в конце ссылки добавьте знак * . 
В этом случае будет сформировано несколько веб-страниц по 50 видео в каждом.
в) Для создания нормальной ссылки из короткой, введите shorts-ссылку.
Для выхода введите 0""")
        pars_yout = ParsingFromYoutube(bot, message)
        bot.register_next_step_handler(message, callback=pars_yout.parsing_from_youtube)
    elif command == "about_IP":

        def search_ip(message):
            pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            ip = message.text
            if ip == "*":
                bot.send_message(message.from_user.id, 'Пожалуйста, выберите команду из /menu')
            elif re.match(pattern, ip):
                url = f"http://ip-api.com/json/{ip}"
                res = requests.get(url).json()
                res.update({"again?": "/about_IP"})
                text = json.dumps(res, indent=4)
                bot.send_message(message.from_user.id, text)
                bot.send_message(message.from_user.id, 'Пожалуйста, выберите команду из /menu')
            else:
                bot.send_message(message.from_user.id, "Это не IP адрес. Попробуйте еще раз. Для выхода введите *")
                bot.register_next_step_handler(message, callback=search_ip)

        bot.send_message(message.from_user.id, "Введите IP адрес:")
        bot.register_next_step_handler(message, callback=search_ip)



@bot.message_handler(content_types=['text'])
def get_text_messages(message: telebot) -> None:
    """Функция интерактивного диалога с пользователем в режиме реакции на любой текст."""

    user_id = message.from_user.id
    print(f'{user_id = }:', message.text)
    if user_id != my_uid:
        bot.send_message(my_uid, f"{user_id}: {message.text}")

    # bot.send_message('99260242', message.text)
    if message.text.lower() in ['привет', 'hi', 'доров', 'дарофф', 'даров', 'дароф', 'дарова', 'превед', 'превет', 'прю',
                                'ку', 'хай', 'прив', 'прива', 'трям']:
        bot.send_message(message.from_user.id, 'И вам здравствуйте :) Пожалуйста, выберите команду из /menu, '
                                               'чтобы воспользоваться нашим сервисом')
    elif message.text == 'стопбот250':
        bot.send_message(message.from_user.id, 'Бот остановлен')
        bot.stop_polling()
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, выберите команду из /menu')

def main():
    try:
        bot.polling(none_stop=True)
    except Exception as ex:
        logger.error(f'Ошибка соединения, {ex}')
        time.sleep(10)
        logger.info('Перазапуск бота')
        main()


if __name__ == '__main__':
    logging.basicConfig(level=20,
                        format="%(asctime)s || %(name)s || %(levelname)s || %(message)s || %(module)s.%(funcName)s:%(lineno)d")
    logger = logging.getLogger('main_logger')
    logger.info('Запуск бота')
    main()
