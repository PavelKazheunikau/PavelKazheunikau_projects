import asyncio
import aiohttp
import xlsxwriter
from bs4 import BeautifulSoup
import csv
from urllib import parse

base_url = 'https://cars.av.by'
header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/110.0.0.0 YaBrowser/23.3.4.605 Yowser/2.5 Safari/537.36 '}


async def get_html(session, url, params=None):
    try:
        async with session.get(url, headers=header, params=params) as resp:
            if resp.status != 200:
                raise ValueError(f'Сервер не доступен {resp.status} {resp.reason}')
            else:
                return await resp.text()
    except (aiohttp.ClientError, ValueError) as e:
        print(f"Произошла ошибка при извлечении страницы: {e}")
        return None


async def num_pages(html):
    soup = BeautifulSoup(html, 'lxml')
    num_of_pages = int(soup.find('div', class_='filter__show-result').span.text.split()[1]) // 25 + 1
    href = soup.find('a', class_="button button--default", role="button" ).get('href')
    next_page_body = soup.find('a', class_='button button--default').get('href')[:-7]
    # all_instances = parse.urlparse(href)
    # dict_from_query = parse.parse_qs(all_instances.query)

    return num_of_pages, next_page_body


async def parse(html):
    soup = BeautifulSoup(html, 'lxml')
    all_data = soup.find_all('div', class_='listing-item')
    page_data = []
    for car in all_data:
        model = car.find('h3', class_='listing-item__title').find('span').text
        price_usd = car.find('div', 'listing-item__priceusd')
        price_usd_convert = int(price_usd.text.encode('ascii', errors='ignore').decode('utf8').strip('$'))
        price = car.find('div', 'listing-item__price')
        price_convert = int(price.text.encode('ascii', errors='ignore').decode('utf8').strip('.'))
        info = car.find('div', 'listing-item__params').span
        info_convert = int(info.text.encode('ascii', errors='ignore').decode('utf8').strip('.'))
        page_data.append([model, price_usd_convert, price_convert, info_convert])
    await write_csv(page_data)
    return


async def write_csv(data):
    datafile = open('output.csv', 'a', encoding='utf-8', newline='')
    datawriter = csv.writer(datafile, delimiter=';')
    # book = xlsxwriter.Workbook('tabl.xlsx')
    # page = book.add_worksheet('Выборка_2')
    # row = last_row
    # column = 0
    # page.set_column('A:A', 20)
    # page.set_column('B:B', 20)
    # page.set_column('C:C', 50)
    # page.set_column('D:D', 50)
    for row in data:
        # page.write(row, column, item[0])
        # page.write(row, column + 1, item[1])
        # page.write(row, column + 2, item[2])
        # page.write(row, column + 3, item[3])
        # next_page = item[4]
        # print(item[4])
        # row += 1
        datawriter.writerow(row)
    datafile.close()
    print('Данные успешно записаны в файл output')
    return


async def main():
    car_model = input('введите марку автомобиля')
    scrap_url = base_url + car_model

    async with aiohttp.ClientSession() as session:
        html1 = await get_html(session, scrap_url, params=None)
        num_of_pages, next_url_body = await  num_pages(html1)
        tasks = []
        for page in range(1, num_of_pages + 1):
            params = {'page': page}
            if page == 1:
                html = await get_html(session, scrap_url)
            else:
                scrap_url = base_url+next_url_body
                html = await get_html(session, scrap_url, params=params)
            if html is not None:
                task = asyncio.create_task(parse(html))
                tasks.append(task)
                print(f'Считывается страница №{page}')
            else:
                break
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # start = datetime.now()
    asyncio.run(main())
    # print(datetime.now() - start)
