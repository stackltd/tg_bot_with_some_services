# import youtube_dl
from youtube_pars.json_to_html import *
from youtube_pars.banned_url_to_html import *
import os
from zipfile import ZipFile
import jmespath
import gc
import json
import yt_dlp as youtube_dl

class ParsingFromYoutube:
    def __init__(self, bot, message):
        from main import my_uid

        self.my_uid = my_uid
        self.bot = bot
        self.message = message
        self.url = ''
        self.uploader = ''
        self.pattern = r'[\/:*?"<>|]'
        self.title = ''

    def parsing_from_youtube(self, message):
        url_in: str = message.text
        user_id = message.from_user.id
        if user_id != self.my_uid:
            self.bot.send_message(self.my_uid, f"{user_id}: {url_in}")
        print(url_in)
        if "shorts" in url_in and url_in.split("/")[-1] != "shorts":
            url = "https://www.youtube.com/watch?v=" + url_in.split('/')[-1]
            self.bot.send_message(message.from_user.id, url)
            self.bot.send_message(self.message.from_user.id, 'Пожалуйста, выберите команду из /menu')
            return
        elif url_in == '0':
            self.bot.send_message(self.message.from_user.id, 'Пожалуйста, выберите команду из /menu')
            return

        if not url_in.endswith('*'):
            embed_on = False
        else:
            url_in = url_in[:-1]
            embed_on = True
        self.url = url_in
        try:
            assert url_in.startswith('https://www.youtube.com')
            # Получение json для тестовых целей:
            test_mode = False
            if test_mode:
                with open('youtube.json', 'r', encoding='utf-8') as file:
                    result = json.load(file)
            else:
                with youtube_dl.YoutubeDL(params={}) as ydl:
                    self.bot.send_message(message.from_user.id, 'Идет формирование веб-страницы. Просьба подождать')
                    result = ydl.extract_info(url_in, download=False)
                # сериализация json, если необходимо
                if _:= False:
                    with open('youtube.json', 'w', encoding='utf-8') as file:
                        json.dump(result, file, indent=4, ensure_ascii=False)

                if not result or result['entries'][0] is None:
                    self.bot.send_message(message.from_user.id, 'К сожалению, плей-лист не удалось загрузить. '
                                                                'Возможно, в ссылке есть ошибка. '
                                                                'Для перехода к панели выбора команды нажмите /menu')
                    return
            # Получаем автора канала
            if url_in.endswith('featured'):
                uploader = result['entries'][0]['title']
            else:
                uploader = jmespath.compile('entries[*].uploader').search(result)[0]
            self.uploader = re.sub(self.pattern, '', uploader)
            # Определяем, скачиваем ли одиночный плей-лист, или все по ссылке для playlists
            if url_in.endswith('playlists'):
                number = len(result['entries'])
            else:
                number = 1
            # Все функции модуля обходим в данном цикле
            for play_list_numb in range(number):
                # получаем название плей-листа и корректируем json при featured
                if url_in.endswith('featured') or number > 1:
                    res = result['entries'][play_list_numb]
                    self.title = res['title']
                elif number == 1:
                    res = result
                    html = requests.get(self.url).text
                    title = re.findall(r'<title>(.+)</title>', html)
                    self.title = ' '.join(title[0].split()[:-2])

                # Если сделан запрос на встроенное видео, формируем несколько веб-листов кратно block_size
                len_play_list = len(res['entries'])
                if embed_on:
                    block_size = 50
                    start_block = 0
                    stop_block = block_size
                    block_numb = 0
                    for block_numb in range(len_play_list // block_size):
                        json_to_html(data_in=res, block_number=block_numb, start_block=start_block,
                                     stop_block=stop_block, reversed=True, embed_on=embed_on)
                        start_block += block_size
                        stop_block += block_size
                    else:
                        if len_play_list % block_size != 0:
                            block_numb += 1 if len_play_list // block_size > 0 else 0
                            json_to_html(data_in=res, block_number=block_numb, start_block=start_block,
                                         stop_block=len_play_list, reversed=True, embed_on=embed_on)
                else:
                    json_to_html(data_in=res, block_number=0, start_block=0, stop_block=len_play_list,
                                 reversed=True, embed_on=embed_on)

                # json_to_html(res, reversed=True, embed_on=embed_on)
                make_banned_urls()
                print('Создание html выполнено успешно')
                self.__send_zip()
            else:
                self.bot.send_message(self.message.from_user.id, 'Пожалуйста, выберите команду из /menu')
            del result
            gc.collect()

        except AssertionError:
            print('Не url')
            self.bot.send_message(message.from_user.id, 'Ошибка. Введите корректный URL: ')
            self.bot.register_next_step_handler(message, callback=self.parsing_from_youtube)
        except KeyError as ex:
            # raise
            print(f'{ex = }')
            self.bot.send_message(message.from_user.id, 'К сожалению, плей-лист не удалось загрузить. '
                                                        'Возможно, в ссылке есть ошибка. '
                                                        'Для перехода к панели выбора команды нажмите /menu')
        except BaseException as ex:
            # raise
            text_error = f'Что-то пошло не так... {ex}'
            print(text_error)
            self.bot.send_message(self.message.from_user.id, f'{text_error}\nПожалуйста, выберите команду из /menu')

    def __send_zip(self):
        """
        Отправка результата поиска пользователю в виде архива с названием автора канала и темы плей-листа.
        Сохранение результата поиска на сервере
        """

        # удаление символов, с которыми невозможно создать каталог в Windows
        name_res = '-'.join([self.uploader, re.sub(self.pattern, '', self.title)]).replace('.:', '.').rstrip('.')
        # запоминаем путь по умолчанию, переходим во временную папку и так же запоминаем ее
        path_def = os.getcwd()
        os.chdir(os.path.abspath('./youtube_pars/out/'))
        path_out = os.getcwd()
        objects = os.listdir('./')
        # формируем имя папки сохранения всех результатов
        name_res = ''.join([name_res, '.zip'])
        # создаем архив с результатом
        print(f'{name_res = }')
        with ZipFile(name_res, 'w') as file:
            [file.write(obj) for obj in objects if obj != name_res]
        # отправляем архив пользователю телеграм
        with open(name_res, 'rb') as temp:
            self.bot.send_document(self.message.from_user.id, temp)
        # распаковываем архив в папку с результатом всех поисков
        with ZipFile(name_res, 'r') as file:
            os.chdir(path_def + '/youtube_pars/all_res/')
            # заходим в папку с названием канала. Если её нет, то создаём
            if not os.path.isdir(self.uploader):
                os.makedirs(self.uploader)
            os.chdir(self.uploader + '/')
            title = re.sub(self.pattern, '', self.title).replace('.:', '.').rstrip('.')
            # создаем папку с названием плей-листа и распаковываем архив. Если она уже создана, ничего не делаем
            if not os.path.isdir(title):
                os.makedirs(title + '/')
                os.chdir(title + '/')
                file.extractall()
        # удаляем все из временной папки
        os.chdir(path_out)
        objects = os.listdir('./')
        [os.remove(obj) for obj in objects]
        # восстановление исходной директории по умолчанию
        os.chdir(path_def)
