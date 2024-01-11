import asyncio

import aiohttp
import xlsxwriter
from bs4 import BeautifulSoup

base_url = 'https://cars.av.by'
header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/110.0.0.0 YaBrowser/23.3.4.605 Yowser/2.5 Safari/537.36 '}


async def get_html(session, url):
    sess = session
    new_url = url
    try:
        async with session.get(url, headers=header) as resp:
            if resp.status != 200:
                raise ValueError(f'Сервер не доступен {resp.status} {resp.reason}')
            else:
                return await resp.text()
    except (aiohttp.ClientError, ValueError) as e:
        print(f"Произошла ошибка при извлечении страницы: {e}")
        return None


def parse(html):
    soup = BeautifulSoup(html, 'lxml')

    next_page = soup.find('a', class_='button button--default').get('href')
    all_data = soup.find_all('div', class_='listing-item')

    for car in all_data:
        model = car.find('h3', class_='listing-item__title').find('span').text
        price_usd = car.find('div', 'listing-item__priceusd')
        price_usd_convert = int(price_usd.text.encode('ascii', errors='ignore').decode('utf8').strip('$'))
        price = car.find('div', 'listing-item__price')
        price_convert = int(price.text.encode('ascii', errors='ignore').decode('utf8').strip('.'))
        info = car.find('div', 'listing-item__params').span
        info_convert = int(info.text.encode('ascii', errors='ignore').decode('utf8').strip('.'))
        yield model, price_usd_convert, price_convert, info_convert, next_page

async def write_xls(param, last_row):
    book = xlsxwriter.Workbook('tabl.xlsx')
    page = book.add_worksheet('Выборка_2')
    row = last_row
    column = 0
    next_page = ''
    page.set_column('A:A', 20)
    page.set_column('B:B', 20)
    page.set_column('C:C', 50)
    page.set_column('D:D', 50)
    for item in param:
        page.write(row, column, item[0])
        page.write(row, column + 1, item[1])
        page.write(row, column + 2, item[2])
        page.write(row, column + 3, item[3])
        next_page = item[4]
        print(item[4])
        row += 1
    book.close()
    print('Данные успешно записаны в файл tabl')
    return next_page, row


async def main():
    car_model = input('введите марку автомобиля')
    next_page = base_url + car_model
    page = 0
    last_row = 1
    async with aiohttp.ClientSession() as session:
        while True:
            html = await get_html(session, next_page)
            if html is not None:
                next_page, last_row = await write_xls(parse(html), last_row)
                if next_page is None:
                    break
                page += 1
                next_page = base_url + next_page
                print(f'Считывается страница №{next_page}')
            else:
                break


if __name__ == '__main__':
    # start = datetime.now()
    asyncio.run(main())
    # print(datetime.now() - start)
