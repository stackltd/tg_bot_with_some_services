import json
import gc
# import re

def json_to_html(data_in, block_number, start_block, stop_block, reversed, embed_on):
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
            margin-bottom: 10px;
            width: 900px;
          }
          </style>
       </head>
       <body>
          <div class="container">"""
    if data_in is None:
        return

    block_numb = str(block_number + 1)
    name_html = ''.join(['URL', block_numb, '.html'])

    with open(f'./youtube_pars/out/{name_html}', 'w', encoding='utf-8') as file:
        file.write(start)
    step = -1 if reversed else 1
    count = start_block
    count2 = 0
    title = ''
    # print(data_in['entries'])
    data_list = data_in['entries'][::step]
    for video in data_list[start_block:stop_block]:
        count += 1
        try:
            count2 += 1
            upload_date = video['upload_date']
            upload_date = '-'.join([upload_date[6:8], upload_date[4:6], upload_date[:4]])
            description = video['description'].split('\n')
            for index, string in enumerate(description):
                if string:
                    string = ''.join(['<p>', string, '</p>', '\n'])
                description[index] = string
            description = ''.join(description)
            title = title + video['title'] + '\n'
            url = video['webpage_url']
            id_yout = url[url.index('=') + 1:]
            if embed_on:
                embed = f'<iframe width="900" height="580" src="https://www.youtube.com/embed/{id_yout}" ' \
                        f'title="{video["title"]}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; ' \
                        f'encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'
            else:
                embed = video['title'] + '\n'
            text = ''.join([''.join(['<a href=', '"' + url + '"',
                                     f' target="_blank">Видео номер {count}. {upload_date}</a>']), embed,
                            '<p> Просмотров: ' + str(video['view_count']) + '</p> <br>', description, '\n\n'])
            with open(f'./youtube_pars/out/{name_html}', 'a', encoding='utf-8') as file:
                file.write(text)
        except Exception as ex:
            print(ex, count)
    else:
        with open('./youtube_pars/out/titles.txt', 'a', encoding='utf-8') as file:
            file.write(title)

    finishe = """      </div>
       </body>
    </html>"""

    with open(f'./youtube_pars/out/{name_html}', 'a', encoding='utf-8') as file:
        file.write(finishe)

    print(count, count2)