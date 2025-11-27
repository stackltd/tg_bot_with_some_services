import logging
import wikipedia
from wikipedia import DisambiguationError, PageError, WikipediaException
import os
import gtts
import telebot
import random
from telebot import types
import json
import re

wiki_logger = logging.getLogger('wiki')


class Wiki:
    def __init__(self, bot, message, lang, select=True, call_list=False, call_photo=False):
        from main import my_uid

        self.my_uid = my_uid
        self.bot = bot
        self.message = message
        self.res_list = []
        self.select = select
        self.call_list = call_list
        self.call_photo = call_photo
        self.url_photos = []
        self.word = ''
        self.lang = lang
        self.audio_check = False
        self.count_err_photo = 0

    def wiki(self):
        wiki_logger.debug('')
        self.bot.send_message(self.message.from_user.id, 'Введите искомое слово. Если желаете получить аудио-версию '
                                                         'статьи, то в конце слова поставьте знак *, например: книга*\n'
                                                         'Можете выбрать другой язык, добавив к слову префикс, например table/fr')
        wikipedia.set_lang(self.lang)
        self.bot.register_next_step_handler(self.message, callback=self.wiki_list)

    def wiki_list(self, message):
        user_id = message.from_user.id
        if user_id != self.my_uid:
            self.bot.send_message(self.my_uid, f"{user_id}: {message.text}")
        wiki_logger.debug('')
        try:
            # получение списка слов по поиску
            if self.select:
                self.word = message.text  # в слово идет текст только при задании слова, когда нужно выбрать из списка, то
                # данный параметр имеет числовое значение
                if self.word.endswith('*'):
                    self.word = self.word[:-1]
                    self.audio_check = True
                if '/' in self.word:
                    self.lang = self.word[self.word.index('/') + 1:]
                    print(self.lang)
                    wikipedia.set_lang(self.lang)
                    self.word = self.word[:self.word.index('/')]
                    print(self.word)
                print(self.lang)
                try:
                    self.res_list = wikipedia.search(self.word, results=20)
                except BaseException as lang_err:
                    print(lang_err, '\nОшибка выбора языка')
                    wikipedia.set_lang('ru')
                    self.res_list = wikipedia.search(self.word)
                    print(self.lang, self.word, self.res_list)
            try:
                # восстановление списка, в случае выбора команды повтора списка предыдущего поиска
                if self.call_list:
                    # Чтение списка поиска по ID пользователя
                    with open('temp/attr.json') as obj:
                        attr_all_users = json.load(obj)
                    print(f'{message.from_user.id = }')
                    user_attr = attr_all_users[str(message.from_user.id)]
                    self.res_list, self.select, self.word, self.lang, self.audio_check = \
                        map(lambda key: user_attr[key], user_attr)
                # коррекция списка, имеющего строки размером больше 64 байт
                self.res_list = self.res_list[:71]
                self.res_list.sort()
                # print(self.res_list)
                for i, phrase in enumerate(self.res_list):
                    len_item = len(phrase.encode('utf8'))
                    if len_item > 64:
                        phrase_list = list(phrase)
                        print(f"{phrase = }")
                        for count, _ in enumerate(phrase_list):
                            if len(''.join(phrase_list[:-1 - count]).encode('utf8')) <= 64:
                                self.res_list[i] = ''.join(phrase_list[:-(count + 2)])
                                break
                            print(count, end=', ')
                # print(self.res_list)

                tg_markup = types.InlineKeyboardMarkup(row_width=8)
                for words in self.res_list:
                    tg_itembtn1 = types.InlineKeyboardButton(words, callback_data=words)
                    tg_markup.add(tg_itembtn1)
                if self.res_list:
                    self.bot.send_message(message.from_user.id, 'Выберите нужный пункт:', reply_markup=tg_markup)
                else:
                    self.bot.send_message(message.from_user.id,
                                          'Слово не найдено. Для перехода к панели выбора команды нажмите /menu')
                # устранение бага декоратора callback_query_handler, возвращающего предыдущее состояние экземпляра класса
                # сериализация атрибутов экземпляра по ID пользователя перед заходом в callback_query_handler
                attr = {'res_list': self.res_list, 'select': self.select, 'word': self.word,
                        'lang': self.lang, 'audio_check': self.audio_check}

                with open('temp/attr.json') as obj:
                    attr_all_users = json.load(obj)
                attr_all_users.update({str(message.from_user.id): attr})
                with open('temp/attr.json', 'w') as file:
                    json.dump(attr_all_users, file, indent=4)

                @self.bot.callback_query_handler(func=lambda call: True)
                def callback_worker(call):
                    #восстановление атрибутов экземпляра класса по ID пользователя - замена их на актуальное состояние
                    with open('temp/attr.json', 'r') as obj:
                        attr_all_users = json.load(obj)
                    user_attr = attr_all_users[str(call.from_user.id)]
                    self.res_list, self.select, self.word, self.lang, self.audio_check = \
                        map(lambda key: user_attr[key], user_attr)
                    print(f"{self.res_list = }")
                    call.message.text = call.data
                    call.message.from_user.id = call.from_user.id
                    if call.data in self.res_list:
                        print(f"{call.data = }")
                        call.message.text = str(self.res_list.index(call.data) + 1)
                        print(f"{call.data = }")
                        if user_id != self.my_uid:
                            self.bot.send_message(self.my_uid, f"{user_id}: Выбрано слово {call.data}")
                        print(f"{call.message.text = }")
                        self.__wiki_page(call.message)
            except BaseException as ex1:
                # raise
                self.bot.send_message(message.from_user.id, 'Слово не найдено. Попробуйте еще раз')
                self.bot.register_next_step_handler(message, callback=self.wiki_list)
                print(f'{ex1 = }')
        except BaseException as wiki_list_err:
            # raise
            self.bot.send_message(message.from_user.id, 'Ошибка выбора языка. Попробуйте еще раз')
            self.bot.register_next_step_handler(message, callback=self.wiki_list)
            print(f'{wiki_list_err = }')

    def __wiki_page(self, message):
        user_id = message.from_user.id
        if user_id != self.my_uid:
            self.bot.send_message(self.my_uid, f"{user_id}: {message.text}")
        wiki_logger.debug('')
        try:
            text = message.text
            try:
                assert text.isdigit() and len(self.res_list) >= int(text) > 0
                print(text)
                point = int(text)
                text = wikipedia.page(self.res_list[point - 1]).content

                if self.audio_check:
                    try:
                        self.bot.send_message(message.from_user.id, 'Формируется аудиофайл, просьба подождать.')
                        t1 = gtts.gTTS(text, lang=self.lang)
                        t1.save("audio.mp3")
                        with open('audio.mp3', 'rb') as audio:
                            self.bot.send_document(message.from_user.id, audio)
                    except BaseException as ex_aud:
                        print(f'{ex_aud = }')
                if len(text) <= 4096:
                    self.bot.send_message(message.from_user.id, text)
                else:
                    name = self.res_list[point - 1]
                    file_name = ''.join([name, '.txt']).replace('.:', '.')  # устранение бага с .: в имени
                    # устраняем символы, запрещенные при создании имен в ОС Windows
                    pattern = r'[\/:*?"<>|]'
                    file_name = re.sub(pattern, '-', file_name)
                    path_abs = os.path.abspath('docs')
                    file_name_abs = os.path.join(path_abs, file_name)
                    print(f'{file_name_abs = }')
                    try:
                        with open(file_name_abs, 'w', encoding='utf-8') as temp:
                            temp.write(text)
                        with open(file_name_abs, 'r', encoding='utf-8') as temp:
                            self.bot.send_document(message.from_user.id, temp)
                    except BaseException as file_err:
                        print(f'{file_err = }')
                try:
                    images = wikipedia.page(self.res_list[point - 1]).images
                    self.url_photos = [fr'{url}' for url in images if url.endswith('.jpg') or url.endswith('.gif')]
                    self.photo_send(message)
                except Exception as ex:
                    # raise
                    print('Исключение', ex, 'опубликовать фото не удалось')
                # self.bot.send_message(message.from_user.id, 'Для перехода к панели выбора команды нажмите /menu\n'
                #                                             'Для повторного вызова результата поиска нажмите /wiki_list_choose\n'
                #                                             'Другой вариант фотоальбома - нажмите /photo_send')

            except DisambiguationError as ex2:
                print(f'{ex2 = }')
                self.res_list = list(set(ex2.__dict__.get('options')))[:71]
                self.res_list.sort()
                print(self.res_list)
                self.select = False
                self.wiki_list(message)
            except AssertionError as ex3:
                print(f'{ex3 = }')
            except PageError as Page_Error:
                print(f'{Page_Error = }')
                self.select = False
                self.bot.send_message(message.from_user.id, 'К сожалению, такой страницы нет')
                self.wiki_list(message)
            except WikipediaException as too_busy:
                print(f'{too_busy = }')
        except BaseException as wiki_page_err:
            # raise
            print(f'{wiki_page_err = }')

    def photo_send(self, message):
        """
        Публикация фото методом send_media_group. Так как в википедии по неизвестным причинам не все ссылки на
        фото обрабатываются методом send_media_group, то применяется коррекция. Сначала делается попытка опубликовать
        группу с 10 url, в случае неудачи циклически удаляется случайный url из промежуточного списка, как только
        в этом списке все ссылки окажутся валидными, они публикуются, а некорректный url удаляется из общего списка и
        публикуется обычным способом.
        При повторном запросе фото все повторяется заново. В итоге в основном списке останутся только корректные ссылки
        """

        user_id = message.from_user.id
        if user_id != self.my_uid:
            self.bot.send_message(self.my_uid, f"{user_id}: {message.text}")
        wiki_logger.debug('')
        if self.call_photo:
            # Чтение списка фото по ID пользователя
            with open('temp/photos.json', 'r') as obj:
                attr_all_users = json.load(obj)
            photos_dumb = attr_all_users[str(message.from_user.id)]
            number = photos_dumb['number']
            self.url_photos = photos_dumb['urls']
        else:
            number = len(self.url_photos)

        random.shuffle(self.url_photos)
        photos = self.url_photos[:11]
        # print(photos)
        print(f'{len(photos) = }')
        count = 0
        while True:
            count += 1
            err_photo_url = 'К сожалению, опубликовать фото не удалось'
            try:
                if len(photos) != 0 and count > 1:
                    err_photo_url = photos.pop(random.randint(0, len(photos) - 1))
                elif len(photos) == 0:
                    self.bot.send_message(message.from_user.id, 'К сожалению, опубликовать фото не удалось')
                    break
                print(f'{len(photos) = }')
                medias = [telebot.types.InputMediaPhoto(url) for url in photos[:10]]
                self.bot.send_media_group(message.chat.id, media=medias)
                # time.sleep(1.5)
                self.bot.send_message(message.from_user.id, f'Всего {number} фото')
            except BaseException as photos_send_error:
                # print(f'{photos_send_error = }')
                self.count_err_photo += 1
            else:
                if self.count_err_photo != 0:
                    self.bot.send_message(message.from_user.id, err_photo_url, disable_web_page_preview=False)
                    if err_photo_url in self.url_photos:
                        self.url_photos.remove(err_photo_url)
                        self.count_err_photo = 0
                        print(f'{self.count_err_photo = }')
                        print(f'{err_photo_url = }')
                break
        print(f'{count = }')
        print(f'{len(photos) = }')
        print(f'{len(self.url_photos) = }')
        self.bot.send_message(message.from_user.id, 'Для перехода к панели выбора команды нажмите /menu\n'
                                                    'Для повторного вызова результата поиска нажмите /wiki_list_choose\n'
                                                    'Другой вариант фотоальбома - нажмите /photo_send')
        # сериализация списка фото по ID пользователя
        photos_dumb = {'urls': self.url_photos, 'number': number}
        with open('temp/photos.json', 'r') as obj:
            photos_all_users = json.load(obj)
        photos_all_users.update({str(message.from_user.id): photos_dumb})
        with open('temp/photos.json', 'w') as file:
            json.dump(photos_all_users, file, indent=4)
