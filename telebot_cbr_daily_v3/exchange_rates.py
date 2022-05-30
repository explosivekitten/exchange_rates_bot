import requests
from bs4 import BeautifulSoup as bs

# сайт центробанка
CBR_BASE_URL = "https://www.cbr.ru/eng"
# страница с курсами валют
CBR_DAILY_URL = f"{CBR_BASE_URL}/currency_base/daily/"


# функция для парсинга страницы
def parse_cbr_currency_base_daily(s: str) -> (dict, dict):
    # словарь с курсами
    currency_rate = {}
    # словарь с названиями валют (на английском, далее не используются)
    currency_name = {}

    # выбираем парсер
    soup = bs(s, 'html.parser')
    # ищем блок html
    html_c = soup.find('html')
    # в нем ищем body
    body_c = html_c.find('body')
    # в нем ищем main
    div_c_0 = body_c.find('main', id='content')

    # далее доходим до таблицы данных, найдя поочередно нужные блоки
    div_c_1 = div_c_0.find('div', class_='offsetMenu')
    div_c_2 = div_c_1.find('div', class_='container-fluid')
    div_c_3 = div_c_2.find('div', class_='col-md-23 offset-md-1')
    div_c_4 = div_c_3.find('div', class_='table-wrapper')
    div_c_5 = div_c_4.find('div', class_='table')

    # непосредственно данные в таблице
    table_c = div_c_5.find('table', class_='data')
    table_body = table_c.find('tbody')

    # запоминаем все строки таблицы
    rows = table_body.find_all('tr')
    # проходимся в цикле по всем строкам
    for i in range(1, len(rows)):
        row = rows[i]
        # ячейки в текущей строке
        tds = row.find_all('td')

        # трехбуквенный код валюты
        char_code = tds[1].string
        # единицы измерения
        unit = float(tds[2].string.replace(",", ""))
        # курс
        rate = float(tds[4].string.replace(",", ""))
        # название
        name = tds[3].string

        # сохраняем курс и название
        currency_rate[char_code] = rate / unit
        currency_name[char_code] = name

    # добавляем также курс рубля 1 к 1 (для удобства дальнейшего использования)
    currency_rate['RUB'] = 1.0
    return currency_rate, currency_name


# функция для получения актуального курса
def get_actual_rates():
    # запрашиваем страницу
    cbr_daily_response = requests.get(CBR_DAILY_URL)
    # парсим страницу
    currency_rate, currency_name = parse_cbr_currency_base_daily(cbr_daily_response.text)
    return currency_rate


# эта часть не используется (просто для проверки)
if __name__ == '__main__':
    cbr_daily_response = requests.get(CBR_DAILY_URL)
    currency_rate, currency_name = parse_cbr_currency_base_daily(cbr_daily_response.text)
    for k, v in currency_rate.items():
        print(k, f"{v:26}", currency_name[k])



