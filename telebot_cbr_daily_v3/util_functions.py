import datetime
import exchange_rates as er


# функция для чтения названий валют из файла
def read_currency_names():
    filename = 'currencies_list.txt'
    currency_name = {}
    with open(filename, encoding="utf8") as fin:
        for line in fin.readlines():
            char_code, name = line.strip().split('\t')
            currency_name[char_code] = name
    return currency_name


# функция для чтения курса валют за текущий день из файла
# так как курсы обновляются ежедневно, то каждый день достаточно запрашивать и парсить страницу лишь один раз
# далее можно сохранить эти курсы и при следующем использовании бота уже читать данные из файла,
# а не запрашивать страницу
def read_rates():
    # сегодняшний день
    today = datetime.date.today()
    # название фала, в который сохранили курсы за текущий день
    rates_filename = 'daily_rates/' + str(today) + '.txt'
    # словарь с курсами валют
    currency_rate = {}
    # открываем файл и читаем курсы
    with open(rates_filename, 'r', encoding="utf8") as fin:
        for line in fin.readlines():
            row = line.strip().split()
            char_code = row[0]
            rate = row[1]
            currency_rate[char_code] = float(rate)
    return currency_rate


# функция для сохранения курсов за текущий день в файл
def save_rates(currency_rate):
    # сегоднящний день
    today = datetime.date.today()
    # название файла
    rates_filename = 'daily_rates/' + str(today) + '.txt'
    # открываем файл и записываем данные
    with open(rates_filename, 'w', encoding="utf8") as fout:
        for char_code, rate in currency_rate.items():
            print(char_code, rate, file=fout)


# функция для получения курса валют
def get_rates():
    # пробуем сначала прочитать курсы из файла
    try:
        currency_rate = read_rates()
    # если файла еще нет (то есть за сегодня еще не запрашивали курсы)
    except FileNotFoundError:
        # то запрашиваем курсы с сайта
        currency_rate = er.get_actual_rates()
        # и сохраняем их
        save_rates(currency_rate)
    return currency_rate


# эта часть не используется (просто для проверки)
if __name__ == '__main__':
    currency_name = read_currency_names()
    currency_rate = get_rates()
    for k, v in currency_rate.items():
        print(k, v, currency_name[k])
