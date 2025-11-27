import logging
from geopy.geocoders import Nominatim
from geopy.distance import geodesic as dist
import re
import requests

geolocator = Nominatim(user_agent='w')

logger_geo = logging.getLogger('geo')


class Geo:

    def __init__(self, bot, message):
        from main import my_uid

        self.my_uid = my_uid
        self.bot = bot
        self.message = message
        self.text_in = ''
        self.select = True
        self.elevation = False

    def geo(self):
        logger_geo.debug('')
        self.bot.send_message(self.message.from_user.id,
                              'Если хотите узнать:\n a) Название локации по гео-координатам, '
                              'введите координаты через запятую. \n б) Расстояние между локациями,'
                              ' в том числе между объектами внутри населенного пункта, введите '
                              'адреса через дефис с пробелами, например:\n'
                              'Москва, Лужники - Москва, Останкино\n'
                              'в) Чтобы получить гео-координаты, введите адрес локации.')
        self.bot.register_next_step_handler(self.message, callback=self.__geo_searh)

    def __geo_searh(self, message):
        user_id = message.from_user.id
        if user_id != self.my_uid:
            self.bot.send_message(self.my_uid, f"{user_id}: {message.text}")
        logger_geo.debug('')
        if self.select:
            self.text_in = message.text
        print(self.text_in.split(', '))
        pattern = r'^-?\d{1,3}\.\d+$'
        if self.text_in == '*':
            self.bot.send_message(message.from_user.id, 'Для перехода к панели выбора команды нажмите /menu')
        elif all([re.match(pattern, word) if ind <= 1 else True for ind, word in enumerate(self.text_in.split(', '))]):
            try:
                print(self.text_in.split(', ')[0], self.text_in.split(', ')[1])
                Latitude = self.text_in.split(', ')[0]
                Longitude = self.text_in.split(', ')[1]
                print(Latitude, Longitude)
                location = geolocator.reverse(Latitude + "," + Longitude)
                self.bot.send_message(message.from_user.id, location)
                url = f"""https://yandex.ru/maps/?ll={Longitude}%2C{Latitude}&mode=search&sll={Longitude}%2C{Latitude}&text={Latitude}%2C{Longitude}&z=17.39"""
                self.bot.send_message(message.from_user.id, url, disable_web_page_preview=False)
                self.bot.send_message(message.from_user.id, 'Для перехода к панели выбора команды нажмите /menu')
            except BaseException as ex:
                print(f'{ex = }')
                self.select = True
                self.bot.send_message(message.from_user.id, 'Ошибка в данных, попробуйте еще раз')
                self.bot.register_next_step_handler(self.message, callback=self.__geo_searh)
        elif len(self.text_in.split(' - ')) == 2:
            try:
                location1 = geolocator.geocode(self.text_in.split(' - ')[0])
                location2 = geolocator.geocode(self.text_in.split(' - ')[1])
                coord1 = (location1.latitude, location1.longitude)
                coord2 = (location2.latitude, location2.longitude)
                distans = str(dist(coord1, coord2)).split()
                print('Расстояние:', distans)
                distans_out = ' '.join([str(round(float(distans[0]), 2)), distans[1]])
                self.bot.send_message(message.from_user.id, f'Расстояние: {distans_out}')
                # вычисляем разность высот, форму вывода и выводим
                elevations = self.__get_elevation((coord1, coord2))
                diff = elevations[0] - elevations[1]
                if diff > 0:
                    slope = r""" \__ """
                elif diff < 0:
                    slope = r""" __/ """
                else:
                    slope = ''
                self.bot.send_message(message.from_user.id,
                                      f'Высоты над ур. моря (м): {elevations[0]}, {elevations[1]}\n'
                                      f'Разница высот:  {diff}м {slope}')
                self.bot.send_message(message.from_user.id, 'Для перехода к панели выбора команды нажмите /menu')
            except BaseException as ex2:
                print(f'{ex2 =}')
                self.bot.send_message(message.from_user.id, 'Ошибка. Введите корректные данные. Для выхода введите "*"')
                self.bot.register_next_step_handler(self.message, callback=self.__geo_searh)
        else:
            try:
                location = geolocator.geocode(self.text_in)
                coord = [str(item) for item in (location.latitude, location.longitude)]
                self.bot.send_message(message.from_user.id, f'Координаты:')
                self.bot.send_message(message.from_user.id, f'{coord[0]}, {coord[1]}')
                self.select = False
                self.text_in = ', '.join(coord)
                print(self.text_in)
                self.__geo_searh(message)
            except BaseException as ex3:
                # raise
                print(f'{ex3 =}')
                self.bot.send_message(message.from_user.id, 'Ошибка. Введите корректные данные. Для выхода введите "*"')
                self.bot.register_next_step_handler(self.message, callback=self.__geo_searh)

    @staticmethod
    def __get_elevation(coords):
        coord_1 = coords[0]
        coord_2 = coords[1]
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={",".join(map(lambda x: str(x), coord_1))}|{",".join(map(lambda x: str(x), coord_2))}"
            result = requests.get(url, timeout=(3, 3)).json()
            elevations = [value["elevation"] for value in result["results"]]
            return elevations
        except requests.exceptions.ConnectionError as connection_error:
            print(connection_error)
        except requests.exceptions.Timeout as timeout_error:
            print(timeout_error)
