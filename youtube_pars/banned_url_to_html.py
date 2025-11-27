import requests
import re
import os


def url_to_html(url, count):
    text = requests.get(url).text
    text = fr'{text}'

    title = re.findall(r'<title>(.+)</title>', text)
    viewcount = re.findall(r'"simpleText":"(.+)"},"shortViewCount"', text)
    date_out = re.findall(r',"dateText":{"simpleText":"(.+)"},"relativeDateText":{"accessibility":{', text)

    descript = re.findall(r'"shortDescription":(.+),"isCrawlable"', text)
    res = descript[0].split(r'\n\n')
    description = []
    for string in res:
        description.extend(string.split('\\n'))

    url_in_tag = ''.join(['<a class="link" href=', '"', url, '"', f'target="_blank">Видео номер {count}. {date_out[0]}</a>'])
    description = ''.join(['<p>', '<br>'.join(description), '</p>'])
    title = ''.join(['<p>', title[0], '</p>'])
    viewcount = ''.join(['<p> Просмотров: ', viewcount[0], '</p> <br>'])

    return ''.join([url_in_tag, title, viewcount, description])

start = """<!DOCTYPE html>
<html lang="ru">
   <head>
      <meta charset="UTF-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Document</title>
          <style>
              html {
              box-sizing: border-box;
            }

            a {
              color: rgb(142, 33, 33);
              text-decoration: rgb(18, 5, 60);
              display: inline-block;
              padding: 24px 49px;
            }


            body {
              font-family: 'font', sans-serif;
            }

            .container {
              margin: 0 auto;
              padding: 80px 0;
              width: 1170px;
              background-color: #d4d5cc;
              font-size: 130%;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              width: auto;
            }

            p {
              margin: 0;
              margin-bottom: 20px;
              width: 900px;
            }

          </style>
   </head>
   <body>
          <div class="container">"""

finishe = """      </div>
   </body>
</html>"""

def make_banned_urls():
    with open('youtube_pars/banned.txt', 'r') as banned:
        text = banned.read()
    text_list = text.split('\n')

    count = 0
    numbers = 0
    # Проводим поиск до метки конца предыдущего сканирования плей-листа, чтобы получить актуальные данные по 'Refetching'
    for string in text_list[::-1]:
        if 'Refetching' in string:
            numbers += 1
        elif string == 'Создание html выполнено успешно':
            break
    # Удаление веб-листа, если нет 'Refetching', в противном случае, создаем его с базовой html структурой
    if numbers == 0:
        print('нет забаненного контента')
        if os.path.isfile('youtube_pars/out/banned_urls.html'):
            os.remove('youtube_pars/out/banned_urls.html')
        return
    else:
        with open('youtube_pars/out/banned_urls.html', 'w', encoding='utf-8') as file:
            file.write(start)

    # поиск по 'Refetching' до метки конца предыдущего сканирования плей-листа
    for string in text_list[::-1]:
        try:
            if string.find('Refetching') != -1:
                count += 1
                url = f'https://www.youtube.com/watch?v={string.split()[1]}'
                text = url_to_html(url, count)
                print(f'Обработано {count} из {numbers}')
                with open('youtube_pars/out/banned_urls.html', 'a', encoding='utf-8') as file:
                    file.write(text)
            elif string == 'Создание html выполнено успешно':
                break
        except Exception as ex:
            print(ex)
    else:
        with open('youtube_pars/out/banned_urls.html', 'a', encoding='utf-8') as file:
            file.write(finishe)