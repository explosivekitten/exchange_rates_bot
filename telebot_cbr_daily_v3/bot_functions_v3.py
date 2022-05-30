import datetime
from collections import defaultdict
from copy import deepcopy
from util_functions import get_rates, read_currency_names
import telebot

# токен бота
MY_TOKEN = '5155573695:AAG7pVZ0fLJKLyQ_qgSd_rVachZA7l_NheE'
# id пользователя для отправки логов
USER_FTT_ID = 814529006
# стадии пользователя
START, CHOOSE_IN_CURR, INPUT_IN_CURR, CHOOSE_OUT_CNT, CHOOSE_OUT_CURR, INPUT_OUT_CURR, INPUT_AMOUNT = range(7)
"""
START, CHOOSE_IN_CURR, INPUT_IN_CURR, CHOOSE_OUT_CNT, CHOOSE_OUT_CURR, INPUT_OUT_CURR, INPUT_AMOUNT
0       1               2               3               4               5                   6       

0. Старт (выбор действия)   -> 1) [выбран "курс валют"]     Курсы валют
                            -> 0) [выбран "список валют"]   Список доступных валют

1. Курсы (выбор валюты)     -> 2) [выбрана "другая валюта"] Ввод валюты
                            -> 3) [выбрана основная валюта] Выбор количества валют
                            
2. Ввод валюты              -> 3) Выбор количества валют

3. Выбор кол-ва             -> 4) Выбор out-валюты

4. Выбор out-валюты         -> 5) [выбрана "другая валюта"] Ввод валюты
                            -> 6) [выбрана основная валюта] Ввод суммы  (или возврат к 4)
                            
5. Ввод валюты              -> 6) Ввод суммы                            (или возврат к 4)

6. Ввод суммы               -> 0) старт           
"""

# читаем названия валют из файла
currency_name = read_currency_names()
# получаем актуальную информацию о курсах
currency_rate = get_rates()

# стадия пользователя
USER_STATE = defaultdict(lambda: START)
# шаблон, который будем использовать для сохранения параметров запроса курса
EXCHANGE_TEMPLATE = {'from': '', 'to': [], 'cnt': 0, 'amount': 0, 'got': 0}
# словарь с параметрами запроса
NEW_EXCHANGE = defaultdict(lambda: deepcopy(EXCHANGE_TEMPLATE))


# различные сообщения для отправки из бота
HELP_MESSAGE = f'Этот бот позволяет получать актуальую информацию о курсах валют с сайта https://www.cbr.ru и ' \
              f'произвести конвертацию из одной валюты в другую.\n' \
              f'Отправьте /rates и следуйте указаниям, чтобы увидеть курсы валют.\n' \
              f'Отправьте /currencies, чтобы увидеть список доступных валют.\n' \
              f'В любой момент отправьте /restart, чтобы вернуться в начало.\n'
START_MESSAGE = f'Приветствую! Для получения справки по боту отправьте /help\nОстальные команды доступны в меню ниже.'
RESTART_MESSAGE = f'Возвращаемся в начало...'
WRONG_COMMAND_MESSAGE = f'Неправильная команда'
# список всех валют
ALL_CURRENCIES = [char_code for char_code, name in currency_name.items()]
# список всех валют для отправки сообщения из бота
CURR_LIST_MESSAGE = '\n'.join([f"{char_code}\t- {name}" for char_code, name in currency_name.items()])

# список смайликов
EMOJI = {
    "MESSAGE_IN": u'\U00002709',
    "MESSAGE_OUT": u'\U000021AA',
    "HELP": u'\U00002754',
    "BACK": u'\U0001F519',
    "CHANGE": u'\U0001F501',
    "DOLLARS": u'\U0001F4B5',
    "GREEN_CIRCLE": u'\U0001F7E2',
    "WHITE_CIRCLE": u'\U000026AA',
    "DOWN_ARROW": u'\U0001F53D',
    "GLOBE": u'\U0001F310',
    "RHOMBUS": u'\U0001F539',
    "PENCIL": u'\U0000270F',
    "EU": '🇪🇺',
    "GB": '🇬🇧',
    "US": '🇺🇸',
    "RU": '🇷🇺'
}


# функция для генерации клавиатуры
def generate_markup(arr: list):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
    for element in arr:
        markup.add(element)
    return markup


# скрытие клавиатуры
keyboard_hider = telebot.types.ReplyKeyboardRemove()

# КНОПКИ
BT_EXCHANGE_RATES = EMOJI["CHANGE"] + " Курсы валют и конвертер"        # кнопка курсов
BT_SHOW_CURR = EMOJI["GLOBE"] + " Список доступных валют"               # кнопка списка валют
start_keyboard = generate_markup([BT_EXCHANGE_RATES, BT_SHOW_CURR])     # клавиатура с этими кнопками

# список основных валют
MAIN_CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP']
# тот же список, но для кнопок (с добавлением смайлов)
MAIN_CURRENCIES_WITH_EMOJI = [EMOJI["RU"] + ' RUB',
                              EMOJI["US"] + ' USD',
                              EMOJI["EU"] + ' EUR',
                              EMOJI["GB"] + ' GBP'
                              ]
BT_HAND_INPUT = EMOJI["PENCIL"] + " Ввести вручную"                     # кнопка ввода вручную
currencies_keyboard = generate_markup(MAIN_CURRENCIES_WITH_EMOJI + [BT_HAND_INPUT])     # клавиатура с этими кнопками

# список доступных количеств валют для конвертации
CURR_CNT_OPTIONS = ['1', '2', '3']
# тот же список, но для кнопок (со смайлами)
CURR_CNT_OPTIONS_WITH_EMOJI = [EMOJI["RHOMBUS"] + ' 1',
                               EMOJI["RHOMBUS"] + ' 2',
                               EMOJI["RHOMBUS"] + ' 3'
                               ]
curr_cnt_keyboard = generate_markup(CURR_CNT_OPTIONS_WITH_EMOJI)        # клавиатура с этими кнопками

BT_BACK = EMOJI["BACK"] + " Назад"                                      # кнопка назад
input_curr_keyboard = generate_markup([BT_SHOW_CURR, BT_BACK])          # клавиатура в стадии ввода валюты вручную

# запуск бота
bot = telebot.TeleBot(MY_TOKEN, threaded=False)


# функция для конвертации валют
def get_converted_sums(EXCHANGE_DICT):
    reply_message = EMOJI["DOWN_ARROW"]*3 + "\n------------\nКурсы валют:"  # ответное сообщение (часть с курсом валют)
    convert_message = ""                                                    # ответное сообщение (часть с конвертацией)
    char_code_from = EXCHANGE_DICT['from']                                  # валюта "из"
    amount = round(EXCHANGE_DICT['amount'], 3)                              # введенная сумма
    for char_code_to in EXCHANGE_DICT['to']:                                # для каждой выбранной валюты
        rate = currency_rate[char_code_from] / currency_rate[char_code_to]  # вычисляем курс
        reply_message += f"\n1.000 {char_code_from} - {round(rate, 3):.3f} {char_code_to}"  # добавляем текущую валюту
        # добавляем конавертацию введенной суммы
        convert_message += f"\n{amount:.2f} {char_code_from} - {round(rate * amount, 3):.2f} {char_code_to}"
    reply_message += "\n\n------------\nКонвертация валют:" + convert_message
    return reply_message


# получение стадии пользователя
def get_state(message):
    return USER_STATE[message.chat.id]


# обновление стадии пользователя
def update_state(message, state):
    USER_STATE[message.chat.id] = state


# логирование входящего сообщения
def log_to_ftt_in(message, message_type='text'):
    if message.from_user.id != USER_FTT_ID:
        user_nick = message.from_user.username
        dt = datetime.datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d %H:%M:%S')
        emoji = EMOJI["MESSAGE_IN"]
        if message_type == 'text':
            log_text = f"{emoji} {dt}\n{message.from_user.id} (@{user_nick}) send message\n>>>>>>>>>>>>>>>>>>>>\n{message.text}"
            bot.send_message(USER_FTT_ID, text=log_text)
        elif message_type == 'location':
            log_text = f"{emoji} {dt}\n{message.from_user.id} (@{user_nick}) send location\n>>>>>>>>>>>>>>>>>>>>\n{message.location.latitude}, {message.location.longitude}"
            bot.send_message(USER_FTT_ID, text=log_text)
        elif message_type == 'photo':
            log_text = f"{emoji} {dt}\n{message.from_user.id} (@{user_nick}) send photo\n>>>>>>>>>>>>>>>>>>>>\n"
            file_id = message.photo[-1].file_id
            bot.send_photo(USER_FTT_ID, photo=file_id, caption=log_text)


# логирование исходящего сообщения
def log_to_ftt_out(user_id: int, send_text: str):
    if user_id != USER_FTT_ID:
        dt = datetime.datetime.fromtimestamp(int(datetime.datetime.now().timestamp())).strftime('%Y-%m-%d %H:%M:%S')
        emoji = EMOJI["MESSAGE_OUT"]
        log_text = f"{emoji} {dt}\nREPLY TO {user_id}:\n{send_text}"
        bot.send_message(USER_FTT_ID, text=log_text)


# отправка сообщение из бота
def send_message_from_bot(chat_id: int, text: str, reply_markup=None):
    # id пользователя, текст сообщения, клавиатура
    user_id, send_text, markup = chat_id, text, reply_markup
    # логируем сообщение
    log_to_ftt_out(user_id, send_text)
    # отправляем сообщение
    if not markup:
        bot.send_message(user_id, text=send_text)
    else:
        bot.send_message(user_id, text=send_text, reply_markup=markup)


# при получении команды help
@bot.message_handler(commands=['help'])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # отправляем
    send_message_from_bot(chat_id=message.chat.id, text=HELP_MESSAGE)
    # обновляем стадию пользователя
    update_state(message, START)


# при получении команды restart
@bot.message_handler(commands=['restart'])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # отправляем
    send_message_from_bot(chat_id=message.chat.id, text=RESTART_MESSAGE, reply_markup=start_keyboard)
    # обновляем стадию пользователя
    update_state(message, START)


# при получении сообщения в случае, когда пользователь находится в начальной стадии (в стадии старт)
@bot.message_handler(func=lambda message: get_state(message) in [START])
def handle_message_start(message):
    # объявляем, что используем переменную с курсами, определенную вне этой функции
    global currency_rate
    # логируем
    log_to_ftt_in(message)
    # если отправлен "старт"
    if message.text == '/start':
        # то отправляем сообщение с приветствием
        send_message_from_bot(chat_id=message.chat.id, text=START_MESSAGE, reply_markup=start_keyboard)
        # обновляем стадию
        update_state(message, START)
    # если отправлен /rates или нажата соответствующая кнопка
    elif message.text in ('/rates', BT_EXCHANGE_RATES):
        # актуализируем курсы
        currency_rate = get_rates()
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Выберите валюту, из которой хотите конвертировать', reply_markup=currencies_keyboard)
        # обновляем стадию
        update_state(message, CHOOSE_IN_CURR)
    # если отправлен /currencies или нажата соответствующая кнопка
    elif message.text in ['/currencies', BT_SHOW_CURR]:
        # отправляем список валют
        send_message_from_bot(chat_id=message.chat.id, text=CURR_LIST_MESSAGE)
    # иначе выводим сообщение об ошибке
    else:
        send_message_from_bot(chat_id=message.chat.id, text=WRONG_COMMAND_MESSAGE)


# при получении сообщения в случае, когда пользователь находится в стадии выбора in-валюты
@bot.message_handler(func=lambda message: get_state(message) in [CHOOSE_IN_CURR])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # если выбрана одна из основных валют
    if message.text.upper()[-3:] in MAIN_CURRENCIES:
        # формируем новый словарь запроса для конвертации
        NEW_EXCHANGE[message.chat.id] = deepcopy(EXCHANGE_TEMPLATE)
        # запоминаем in-валюту
        NEW_EXCHANGE[message.chat.id]['from'] = message.text.upper()[-3:]
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Теперь выберите количество валют, в которые хотите конвертировать', reply_markup=curr_cnt_keyboard)
        # обновляем стадию
        update_state(message, CHOOSE_OUT_CNT)
    # иначе если выбран ручной ввод
    elif message.text == BT_HAND_INPUT:
        # то отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Введите код валюты (3 буквы). Чтобы посмотреть список кодов, нажмите соответствующую кнопку.', reply_markup=input_curr_keyboard)
        # и обновляем стадию
        update_state(message, INPUT_IN_CURR)
    # иначе выводим сообщение об ошибке
    else:
        send_message_from_bot(chat_id=message.chat.id, text=WRONG_COMMAND_MESSAGE)


# при получении сообщения в случае, когда пользователь находится в стадии ручного ввода in-валюты
@bot.message_handler(func=lambda message: get_state(message) in [INPUT_IN_CURR])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # если нажата кнопка назад
    if message.text == BT_BACK:
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Выберите валюту, из которой хотите конвертировать', reply_markup=currencies_keyboard)
        # и возвращаем стадию
        update_state(message, CHOOSE_IN_CURR)
    # иначе если нажата кнопка показа доступных валют
    elif message.text == BT_SHOW_CURR:
        # то показываем их
        send_message_from_bot(chat_id=message.chat.id, text=CURR_LIST_MESSAGE)
    # иначе если выбрана одна из доступных валют
    elif message.text.upper() in ALL_CURRENCIES:
        # формируем новый словарь для конвертации
        NEW_EXCHANGE[message.chat.id] = deepcopy(EXCHANGE_TEMPLATE)
        # запоминаем in-валюту
        NEW_EXCHANGE[message.chat.id]['from'] = message.text.upper()
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Теперь выберите количество валют, в которые хотите конвертировать', reply_markup=curr_cnt_keyboard)
        # обновляем стадию
        update_state(message, CHOOSE_OUT_CNT)
    # иначе выводим сообщение об ошибке
    else:
        send_message_from_bot(chat_id=message.chat.id, text=WRONG_COMMAND_MESSAGE)


# при получении сообщения в случае, когда пользователь находится в стадии выбора количества out-валют
@bot.message_handler(func=lambda message: get_state(message) in [CHOOSE_OUT_CNT])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # если выбрано одно из доступных количеств
    if message.text[-1] in CURR_CNT_OPTIONS:
        curr_cnt = int(message.text[-1])
        # запоминаем количество out-валют
        NEW_EXCHANGE[message.chat.id]['cnt'] = curr_cnt
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Выберите валюту, в которую хотите конвертировать (1/{curr_cnt})\n'
                                                            f'{EMOJI["GREEN_CIRCLE"]}{EMOJI["WHITE_CIRCLE"]*(curr_cnt - 1)}', reply_markup=currencies_keyboard)
        # обновляем стадию
        update_state(message, CHOOSE_OUT_CURR)
    # иначе выводим сообщение об ошибке
    else:
        send_message_from_bot(chat_id=message.chat.id, text=WRONG_COMMAND_MESSAGE)


# при получении сообщения в случае, когда пользователь находится в стадии выбора out-валюты
@bot.message_handler(func=lambda message: get_state(message) in [CHOOSE_OUT_CURR])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # если выбрана одна из основных валют
    if message.text.upper()[-3:] in MAIN_CURRENCIES:
        # увеличиваем счетчик выбранных валют
        NEW_EXCHANGE[message.chat.id]['got'] += 1
        # сохраняем выбранную валюту
        NEW_EXCHANGE[message.chat.id]['to'].append(message.text.upper()[-3:])
        # колиечство запрошенных out-валют
        curr_cnt = NEW_EXCHANGE[message.chat.id]['cnt']
        # количество уже выбранных out-валют
        got_so_far = NEW_EXCHANGE[message.chat.id]['got']
        # если пока выбрано менее, чем запрошено
        if got_so_far < curr_cnt:
            # то отправляем сообщение для выбора очередной валюты
            send_message_from_bot(chat_id=message.chat.id, text=f'Выберите валюту, в которую хотите конвертировать ({got_so_far + 1}/{curr_cnt})\n'
                                                                f'{EMOJI["GREEN_CIRCLE"] * (got_so_far + 1)}{EMOJI["WHITE_CIRCLE"]*(curr_cnt - got_so_far - 1)}', reply_markup=currencies_keyboard)
        # иначе
        else:
            # отправляем сообщение для ввода суммы для конвертации
            send_message_from_bot(chat_id=message.chat.id, text=f'Введите сумму для конвертации (не более 1 000 000 у.е., дробную часть отделяйте точкой)', reply_markup=keyboard_hider)
            # обновляем стадию
            update_state(message, INPUT_AMOUNT)
    # если нажата кнопка ручного ввода
    elif message.text == BT_HAND_INPUT:
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Введите код валюты (3 буквы). Чтобы посмотреть список кодов, нажмите соответствующую кнопку.', reply_markup=input_curr_keyboard)
        # обновляем стадию
        update_state(message, INPUT_OUT_CURR)
    # иначе выводим сообщение об ошибке
    else:
        send_message_from_bot(chat_id=message.chat.id, text=WRONG_COMMAND_MESSAGE)


# при получении сообщения в случае, когда пользователь находится в стадии ручного ввода out-валюты
@bot.message_handler(func=lambda message: get_state(message) in [INPUT_OUT_CURR])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    # количество запрошенных out-валют
    curr_cnt = NEW_EXCHANGE[message.chat.id]['cnt']
    # количество уже выбранных out-валют
    got_so_far = NEW_EXCHANGE[message.chat.id]['got']
    if message.text == BT_BACK:
        # отправляем сообщение
        send_message_from_bot(chat_id=message.chat.id, text=f'Выберите валюту, в которую хотите конвертировать ({got_so_far + 1}/{curr_cnt})\n'
                                                            f'{EMOJI["GREEN_CIRCLE"] * (got_so_far + 1)}{EMOJI["WHITE_CIRCLE"]*(curr_cnt - got_so_far - 1)}', reply_markup=currencies_keyboard)
        # обновляем стадию
        update_state(message, CHOOSE_OUT_CURR)
    # иначе если нажата кнопка показа доступных валют
    elif message.text == BT_SHOW_CURR:
        # то показываем их
        send_message_from_bot(chat_id=message.chat.id, text=CURR_LIST_MESSAGE)
    # иначе если выбрана одна из основных валют
    elif message.text.upper() in ALL_CURRENCIES:
        # увеличиваем счетчик выбранных валют
        NEW_EXCHANGE[message.chat.id]['got'] += 1
        # сохраняем выбранную валюту
        NEW_EXCHANGE[message.chat.id]['to'].append(message.text.upper())
        # колиечство запрошенных out-валют
        curr_cnt = NEW_EXCHANGE[message.chat.id]['cnt']
        # колиечство уже выбранных out-валют
        got_so_far = NEW_EXCHANGE[message.chat.id]['got']
        # если пока выбрано менее, чем запрошено
        if got_so_far < curr_cnt:
            # отправляем сообщение для выбора очередной валюты
            send_message_from_bot(chat_id=message.chat.id, text=f'Выберите валюту, в которую хотите конвертировать ({got_so_far + 1}/{curr_cnt})\n'
                                                                f'{EMOJI["GREEN_CIRCLE"] * (got_so_far + 1)}{EMOJI["WHITE_CIRCLE"]*(curr_cnt - got_so_far - 1)}', reply_markup=currencies_keyboard)
            # обновляем стадию
            update_state(message, CHOOSE_OUT_CURR)
        # иначе
        else:
            # отправляем сообщение для ввода суммы для конвертации
            send_message_from_bot(chat_id=message.chat.id, text=f'Введите сумму для конвертации (не более 1 000 000 у.е., дробную часть отделяйте точкой)', reply_markup=keyboard_hider)
            # обновляем стадию
            update_state(message, INPUT_AMOUNT)
    # иначе выводим сообщение об ошибке
    else:
        send_message_from_bot(chat_id=message.chat.id, text=WRONG_COMMAND_MESSAGE)


# при получении сообщения в случае, когда пользователь находится в стадии ввода суммы для конвертации
@bot.message_handler(func=lambda message: get_state(message) in [INPUT_AMOUNT])
def handle_message_start(message):
    # логируем
    log_to_ftt_in(message)
    try:
        # пробуем перевести выбранное сообщение в десятичное число
        amount = float(message.text)
        # если сумма в нужном диапазоне
        if 0 < amount <= 1_000_000:
            # то сохраняем сумму
            NEW_EXCHANGE[message.chat.id]['amount'] = amount
            # формируем ответное сообщение с курсом валют и конвертацией
            reply_message = get_converted_sums(NEW_EXCHANGE[message.chat.id])
            # отправляем это сообщение
            send_message_from_bot(chat_id=message.chat.id, text=reply_message, reply_markup=start_keyboard)
            # обновляем стадию
            update_state(message, START)
        # иначе отправляем сообщение об ошибке
        else:
            send_message_from_bot(chat_id=message.chat.id, text=f'Неправильная сумма, введите заново')
    # если введено НЕ десятичное число, то тоже выводим ошибку
    except ValueError:
        send_message_from_bot(chat_id=message.chat.id, text=f'Неправильный формат суммы, введите заново')


# запускаем бота
try:
    bot.polling()
except telebot.apihelper.ApiException:
    pass

