import telebot
from telebot import types
import sqlite3
import config
import requests
import json
import logging

bot = telebot.TeleBot(config.TOKEN)
user_state = {}
user_data = {}


# Функция для подключения к базе данных
def get_db_connection():
    return sqlite3.connect("C:/Users/Redmi/OneDrive/Рабочий стол/pp/work_bd.db", check_same_thread=False)


# Функция регистрации пользователя
def register_user(user_id, first_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            was TEXT DEFAULT '',
            favorites TEXT DEFAULT ''
        )
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)
    """,
        (user_id, first_name),
    )
    conn.commit()
    conn.close()


# Добавление в БД нового места
def save_to_db_new_place(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS places_events_na_proverky (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL
            );
        """
        )
        data = user_data[user_id]
        cursor.execute(
            "INSERT INTO places_events_na_proverky (name, type, description) VALUES (?, ?, ?)",
            (data["name"], data["type"], data["description"]),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


# Добавление комментариев
def add_comment_to_db(place_id, user_id, text, sentiment_score):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id INTEGER,
            user_id INTEGER,
            text TEXT,
            sentiment_score INTEGER
        );
    """
    )
    cursor.execute(
        "INSERT INTO comments (place_id, user_id, text, sentiment_score) VALUES (?, ?, ?, ?)",
        (place_id, user_id, text, sentiment_score),
    )
    conn.commit()
    conn.close()


# Функция получения мест по типу
def get_places_by_type(user_id, place_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT was FROM users WHERE user_id = ?", (user_id,))
    was_raw = cursor.fetchone()
    was = was_raw[0].split(",") if was_raw and was_raw[0] else []
    cursor.execute(
        """
        SELECT id, name, description FROM places_events
        WHERE type LIKE ?
    """,
        (f"%{place_type}%",),
    )
    places = [p for p in cursor.fetchall() if str(p[0]) not in was]
    conn.close()
    return places


# Функция получения списка посещенных мест
def get_was_list(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT was FROM users WHERE user_id = ?", (user_id,))
    was_raw = cursor.fetchone()
    was = was_raw[0].split(",") if was_raw and was_raw[0] else []
    if not was:
        conn.close()
        return []
    placeholders = ",".join("?" for _ in was)
    cursor.execute(
        f"""
        SELECT id, name, description FROM places_events
        WHERE id IN ({placeholders})
    """,
        was,
    )
    places = cursor.fetchall()
    conn.close()
    return places


# Функция получения избранных мест
def get_favorites(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT favorites FROM users WHERE user_id = ?", (user_id,))
    fav_raw = cursor.fetchone()
    fav = fav_raw[0].split(",") if fav_raw and fav_raw[0] else []
    if not fav:
        conn.close()
        return []
    placeholders = ",".join("?" for _ in fav)
    cursor.execute(
        f"""
        SELECT id, name, description FROM places_events
        WHERE id IN ({placeholders})
    """,
        fav,
    )
    places = cursor.fetchall()
    conn.close()
    return places


# Функция отметки места как посещенного
def mark_as_visited(user_id, place_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT was FROM users WHERE user_id = ?", (user_id,))
    was_raw = cursor.fetchone()
    was = set(was_raw[0].split(",")) if was_raw and was_raw[0] else set()
    was.add(str(place_id))
    cursor.execute(
        "UPDATE users SET was = ? WHERE user_id = ?", (",".join(was), user_id)
    )
    cursor.execute("SELECT favorites FROM users WHERE user_id = ?", (user_id,))
    fav_raw = cursor.fetchone()
    fav = set(fav_raw[0].split(",")) if fav_raw and fav_raw[0] else set()
    fav.discard(str(place_id))
    cursor.execute(
        "UPDATE users SET favorites = ? WHERE user_id = ?",
        (",".join(fav), user_id),
    )
    conn.commit()
    conn.close()


# Функция удаления отметки о посещении
def unmark_as_visited(user_id, place_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT was FROM users WHERE user_id = ?", (user_id,))
    was_raw = cursor.fetchone()
    was = set(was_raw[0].split(",")) if was_raw and was_raw[0] else set()
    was.discard(str(place_id))
    cursor.execute(
        "UPDATE users SET was = ? WHERE user_id = ?", (",".join(was), user_id)
    )
    conn.commit()
    conn.close()


# Функция добавления в избранное
def mark_as_favorite(user_id, place_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT favorites FROM users WHERE user_id = ?", (user_id,))
    fav_raw = cursor.fetchone()
    fav = set(fav_raw[0].split(",")) if fav_raw and fav_raw[0] else set()
    fav.add(str(place_id))
    cursor.execute(
        "UPDATE users SET favorites = ? WHERE user_id = ?",
        (",".join(fav), user_id),
    )
    conn.commit()
    conn.close()


# Функция оценки места
def rate_place(user_id, place_id, score):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ratings (
            user_id INTEGER,
            place_id INTEGER,
            score INTEGER,
            PRIMARY KEY (user_id, place_id)
        )
    """
    )
    cursor.execute(
        """
        REPLACE INTO ratings (user_id, place_id, score) VALUES (?, ?, ?)
    """,
        (user_id, place_id, score),
    )
    conn.commit()
    conn.close()


# Функция получения средней оценки
def get_avg_rating(place_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT AVG(score) FROM ratings WHERE place_id = ?", (place_id,)
    )
    avg = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM ratings WHERE place_id = ?", (place_id,)
    )
    count = cursor.fetchone()[0]

    conn.close()

    if avg is None:
        return "Ещё нет оценок"

    stars = round(avg / 2)
    star_rating = "★" * stars + "☆" * (5 - stars)

    return f"{star_rating} {round(avg, 1)}/10 (оценок: {count})"


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def handle_start(message):
    register_user(message.from_user.id, message.from_user.first_name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Найти место", "Уже был")
    markup.add("Добавить место", "Посмотреть избранное")
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! Я помогу подобрать место для досуга.\nЕсли хотите узнать про мероприятие подробнее и получить адрес, то просто напишите <Расскажи про (название места как в карточке)>.",
        reply_markup=markup
    )


# Обработчик запросов к Yandex GPT (исправленная версия)
@bot.message_handler(func=lambda m: m.text.lower().startswith("расскажи про "))
def handle_yandex_gpt_request(message):
    place = message.text[13:].strip()

    if not place:
        bot.reply_to(message, "Пожалуйста, укажите место после 'Расскажи про'")
        return

    try:
        response = requests.post(
            url="https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Api-Key {config.YANDEX_API_KEY}",
                "x-folder-id": config.YANDEX_FOLDER_ID,
                "Content-Type": "application/json",
            },
            json={
                "modelUri": f"gpt://{config.YANDEX_FOLDER_ID}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.6,
                    "maxTokens": "2000",
                },
                "messages": [
                    {
                        "role": "user",
                        "text": f"Расскажи максимально подробно про {place}. Укажи точный адрес и сформируй ссылку на Яндекс.Карты в формате: 'Ссылка на карты: https://yandex.ru/maps/?text={place}'",
                    }
                ],
            },
        )

        response.raise_for_status()
        result = response.json()
        answer = result["result"]["alternatives"][0]["message"]["text"]
        bot.reply_to(message, answer)

    except Exception as e:
        print(f"Ошибка при запросе к YandexGPT: {e}")
        bot.reply_to(
            message,
            "Произошла ошибка при обработке запроса. Попробуйте позже.",
        )


# Остальные обработчики сообщений
@bot.message_handler(func=lambda m: m.text == "Найти место")
def handle_find_place(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Кино", "Театр", "Музей")
    markup.add("Прогулка", "Ресторан", "Меню")
    bot.send_message(
        message.chat.id,
        "Куда бы вы хотели сходить? Посмотрите на кнопки ниже.",
        reply_markup=markup,
    )


@bot.message_handler(func=lambda m: m.text == "Меню")
def handle_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Найти место", "Уже был")
    markup.add("Добавить место", "Посмотреть избранное")
    bot.send_message(
        message.chat.id,
        f"Если хотите узнать про мероприятие подробнее и получить адрес, то просто напишите <Расскажи про (название места как в карточке)>.",
        reply_markup=markup,
    )


@bot.message_handler(func=lambda m: m.text == "Уже был")
def handle_was_list(message):
    user_id = message.from_user.id
    user_state[user_id] = {"view": "was", "index": 0}
    show_was(message.chat.id, user_id)


@bot.message_handler(func=lambda m: m.text == "Добавить место")
def insert_place(message):
    user_id = message.from_user.id
    user_data[user_id] = {
        "name": None,
        "type": None,
        "description": None,
        "step": None,
    }
    show_keyboard(
        message.chat.id,
        "Для внесения места добавьте информацию о месте в соотвествии с предложенными кнопками.",
    )


@bot.message_handler(func=lambda m: m.text == "Посмотреть избранное")
def handle_view_favorites(message):
    user_id = message.from_user.id
    fav_list = get_favorites(user_id)
    if not fav_list:
        bot.send_message(
            message.chat.id,
            "Избранных мероприятий нет.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                "Меню"
            ),
        )
        return
    user_state[user_id] = {"view": "favorites", "index": 0}
    show_favorites(message.chat.id, user_id)


@bot.message_handler(
    func=lambda m: m.text in ["Кино", "Театр", "Музей", "Прогулка", "Ресторан"]
)
def handle_category(message):
    user_id = message.from_user.id
    user_state[user_id] = {
        "view": "browse",
        "category": message.text.lower(),
        "index": 0,
    }
    show_place(message.chat.id, user_id)


# Функции отображения информации
def show_was(chat_id, user_id, message_id=None):
    state = user_state.get(user_id)
    if not state or state.get("view") != "was":
        return
    places = get_was_list(user_id)
    if not places:
        bot.send_message(
            chat_id,
            "Список пуст.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                "Меню"
            ),
        )
        return
    idx = state["index"] % len(places)
    place = places[idx]
    rating = get_avg_rating(place[0])
    caption = f"{place[1]}\n\n{place[2]}\n\nРейтинг: {rating}"
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("⬅️", callback_data="prev"),
        types.InlineKeyboardButton("Меню", callback_data="menu"),
        types.InlineKeyboardButton("➡️", callback_data="next"),
    )
    kb.add(
        types.InlineKeyboardButton(
            "Убрать из уже был", callback_data=f"unwas_{place[0]}"
        )
    )

    if message_id:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=caption,
                reply_markup=kb,
            )
        except:
            bot.send_message(chat_id, caption, reply_markup=kb)
    else:
        bot.send_message(chat_id, caption, reply_markup=kb)


def show_place(chat_id, user_id, message_id=None):
    state = user_state.get(user_id)
    if not state or state.get("view") != "browse":
        return
    places = get_places_by_type(user_id, state["category"])
    if not places:
        bot.send_message(
            chat_id,
            "Нет доступных мест в этой категории.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                "Меню"
            ),
        )
        return
    idx = state["index"] % len(places)
    place = places[idx]
    rating = get_avg_rating(place[0])
    caption = f"{place[1]}\n\n{place[2]}\n\nРейтинг: {rating}"
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("⬅️", callback_data="prev"),
        types.InlineKeyboardButton(
            "В избранное", callback_data=f"fav_{place[0]}"
        ),
        types.InlineKeyboardButton("➡️", callback_data="next"),
    )
    kb.row(
        types.InlineKeyboardButton(
            "Добавить отзыв", callback_data=f"add_comment_{place[0]}"
        ),
        types.InlineKeyboardButton(
            "Добавить оценку", callback_data=f"rate_{place[0]}"
        ),
    )
    kb.add(
        types.InlineKeyboardButton("Уже был", callback_data=f"was_{place[0]}"),
        types.InlineKeyboardButton(
            "Комментарии", callback_data=f"get_summary_{place[0]}"
        ),
    )

    if message_id:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=caption,
                reply_markup=kb,
            )
        except:
            bot.send_message(chat_id, caption, reply_markup=kb)
    else:
        bot.send_message(chat_id, caption, reply_markup=kb)


def show_favorites(chat_id, user_id, message_id=None):
    state = user_state.get(user_id)
    if not state or state.get("view") != "favorites":
        return
    places = get_favorites(user_id)
    if not places:
        bot.send_message(
            chat_id,
            "Избранных мероприятий нет.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                "Меню"
            ),
        )
        return
    idx = state["index"] % len(places)
    place = places[idx]
    rating = get_avg_rating(place[0])
    caption = f"{place[1]}\n\n{place[2]}\n\nРейтинг: {rating}"
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("⬅️", callback_data="prev"),
        types.InlineKeyboardButton("Меню", callback_data="menu"),
        types.InlineKeyboardButton("➡️", callback_data="next"),
    )
    kb.add(
        types.InlineKeyboardButton("Уже был", callback_data=f"was_{place[0]}")
    )

    if message_id:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=caption,
                reply_markup=kb,
            )
        except:
            bot.send_message(chat_id, caption, reply_markup=kb)
    else:
        bot.send_message(chat_id, caption, reply_markup=kb)


def show_keyboard(chat_id, message_text=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Название", "Категория", "Описание")
    markup.add("Сохранить место", "Отмена")
    if message_text:
        bot.send_message(chat_id, message_text, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(
    func=lambda m: m.chat.id in user_data
    and m.text in ["Название", "Категория", "Описание"]
)
def ask_for_data(message):
    user_id = message.chat.id
    if message.text == "Название":
        user_data[user_id]["step"] = "name"
        bot.send_message(
            user_id,
            "Введите название места:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == "Категория":
        user_data[user_id]["step"] = "type"
        bot.send_message(
            user_id,
            "Напишите одну или несколько категорий из предложенных:\n▪️кино\n▪️театр\n▪️музей\n▪️прогулка\n▪️ресторан",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == "Описание":
        user_data[user_id]["step"] = "description"
        bot.send_message(
            user_id,
            "Введите описание места в формате 1-2 предложений с отличительными качествами места:",
            reply_markup=types.ReplyKeyboardRemove(),
        )


@bot.message_handler(
    func=lambda m: m.chat.id in user_data and m.text == "Отмена"
)
def cancel_adding(message):
    user_id = message.chat.id
    if user_id in user_data:
        del user_data[user_id]
    handle_menu(message)


@bot.message_handler(
    func=lambda m: m.chat.id in user_data
    and user_data.get(m.chat.id, {}).get("step")
)
def save_data(message):
    user_id = message.chat.id
    step = user_data[user_id]["step"]
    user_data[user_id][step] = message.text
    user_data[user_id]["step"] = None
    show_keyboard(user_id, "Выберите следующее действие.")


@bot.message_handler(
    func=lambda m: m.chat.id in user_data and m.text == "Сохранить место"
)
def save_place(message):
    user_id = message.chat.id
    if user_id not in user_data:
        return

    data = user_data[user_id]
    if None in [data["name"], data["type"], data["description"]]:
        show_keyboard(user_id, "Заполните все поля перед сохранением!")
        return

    if save_to_db_new_place(user_id):
        bot.send_message(
            user_id,
            "Ваше место успешно добавлено🎉\nНа данный момент оно находится на проверке, наш модератор уточняет достоверность введенных Вами данных и вдальнейшем разместит его в Telegram-боте в разделе 'Найти место'😊",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        del user_data[user_id]
        handle_menu(message)
    else:
        show_keyboard(user_id, "Ошибка сохранения. Попробуйте снова.")


# Функция анализа комментария от пользователя
def analyze_komm(text):
    prompt = (
        f'Внимательно проанализируй следующий текст:\n"{text}"\n\n'
        "Если в тексте есть матерные или оскорбительные выражения, "
        "нецезурная(ненормативная) лексика, слова выходящие из культурного лексикона или "
        "присутсвуют слова не имеющие смысл или не относящиеся к контексту, бессвязный набор русских или английских букв, которые невозможно "
        "интерпритировать как осмысленные слова, например,  ыалыоалоыаиб, саацащц, csnck, chsifcisfhcisufhr, sodcjnso, JGDf?, выа, "
        "оиРИПВИ св, курлык и аналогичные им, а также текст, который нельзя отнетсти к категории отзыва о месте то contains_profanity - true, иначе — false.\n"
        "Определи также тональность, если можно распознать смысл написанного и тональность позитивная пиши 1, "
        "если негативная пиши 2\n\n"
        "Ответь строго в формате JSON:\n"
        "{\n"
        '  "contains_profanity": true/false,\n'
        '  "sentiment": "1/2"\n'
        "}"
    )
    headers = {
        "Authorization": f"Bearer {config.YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "modelUri": f"gpt://{config.YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 200,
        },
        "messages": [{"role": "user", "text": prompt}],
    }
    try:
        response = requests.post(
            config.API_ENDPOINT, json=data, headers=headers
        )
        if response.status_code != 200:
            logging.error(
                f"Ошибка при запросе к YandexGPT. Статус код: {response.status_code}, Текст: {response.text}"
            )
            return False, -1
        result = response.json()
        output_text = (
            result["result"]["alternatives"][0]["message"]["text"]
            .strip()
            .replace("```", "")
            .strip()
        )
        logging.info(f"YandexGPT response: {output_text}")
        analysis = json.loads(output_text)
        sentiment = analysis.get("sentiment", "неизвестно")
        contains_profanity = analysis.get("contains_profanity", False)
        sentiment_score = int(sentiment) if sentiment in ("1", "2") else -1
        return contains_profanity, sentiment_score
    except Exception as e:
        logging.error(f"Ошибка при анализе комментария: {e}")
        return False, -1


def get_reviews_summary(place_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT text, sentiment_score FROM comments WHERE place_id = ?",
        (place_id,),
    )
    reviews = cursor.fetchall()
    conn.close()
    if not reviews:
        return "Нет отзывов для этого места."
    good_reviews = [r[0] for r in reviews if r[1] == 1]
    bad_reviews = [r[0] for r in reviews if r[1] == 2]

    good_summary = summarize_reviews(good_reviews, "good")
    bad_summary = summarize_reviews(bad_reviews, "bad")

    return good_summary, bad_summary


def summarize_reviews(reviews, sentiment_type):
    if not reviews:
        return f"Нет {'положительных' if sentiment_type == 'good' else 'отрицательных'} отзывов."
    if sentiment_type == "good":
        prompt = (
            f"Проанализируй положительные отзывы о месте и выдели основные моменты:\n\n"
            f"Отзывы:\n{chr(10).join(reviews[:5])}\n\n"
            "Сделай тезисно краткий анализ, выделив основные преимущества, "
            "которые отмечают посетители. Ответ должен быть структурированным и информативным."
        )
    else:
        prompt = (
            f"Проанализируй отрицательные отзывы о месте и выдели основные проблемы:\n\n"
            f"Отзывы:\n{chr(10).join(reviews[:5])}\n\n"
            "Сделай тезисно краткий анализ выделив основные недостатки, "
            "которые отмечают посетители. Ответ должен быть конструктивным."
        )
    headers = {
        "Authorization": f"Bearer {config.YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "modelUri": f"gpt://{config.YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.4,
            "maxTokens": 500,
        },
        "messages": [{"role": "user", "text": prompt}],
    }
    try:
        response = requests.post(
            config.API_ENDPOINT, json=data, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        summary = result["result"]["alternatives"][0]["message"]["text"]
        return summary
    except Exception as e:
        logging.error(f"Ошибка при генерации сводки: {e}")
        return f"Не удалось проанализировать {'положительные' if sentiment_type == 'good' else 'отрицательные'} отзывы."


@bot.message_handler(func=lambda m: m.text == "Посмотреть избранное")
def handle_view_favorites(message):
    user_id = message.from_user.id
    fav_list = get_favorites(user_id)
    if not fav_list:
        bot.send_message(
            message.chat.id,
            "Избранных мероприятий нет.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                "Меню"
            ),
        )
        return
    user_state[user_id] = {"view": "favorites", "index": 0}
    show_favorites(message.chat.id, user_id)


# Обработчик callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data

    if data == "next":
        user_state[user_id]["index"] += 1
    elif data == "prev":
        user_state[user_id]["index"] -= 1
    elif data == "menu":
        handle_menu(call.message)
        return
    elif data.startswith("fav_"):
        place_id = int(data.split("_")[1])
        mark_as_favorite(user_id, place_id)
        bot.answer_callback_query(call.id, "Добавлено в избранное")
        return
    elif data.startswith("was_"):
        place_id = int(data.split("_")[1])
        mark_as_visited(user_id, place_id)
        bot.answer_callback_query(call.id, "Отмечено как посещённое")
    elif data.startswith("unwas_"):
        place_id = int(data.split("_")[1])
        unmark_as_visited(user_id, place_id)
        bot.answer_callback_query(call.id, "Удалено из списка посещённых")
        show_was(call.message.chat.id, user_id, call.message.message_id)
        return
    elif data.startswith("rate_"):
        place_id = int(data.split("_")[1])
        bot.send_message(call.message.chat.id, "Оцените это место от 0 до 10")
        bot.register_next_step_handler(call.message, process_rating, place_id)
        return
    elif data.startswith("add_comment_"):
        place_id = int(data.split("_")[2])
        msg = bot.send_message(
            call.message.chat.id, "Напишите ваш комментарий:"
        )
        bot.register_next_step_handler(msg, process_comment_step, place_id)
        return
    elif data.startswith("get_summary_"):
        place_id = int(call.data.split("_")[2])
        good_summary, bad_summary = get_reviews_summary(place_id)

        response = f"\n✅ {good_summary}\n" f"\n❌ {bad_summary}\n"

        bot.send_message(call.message.chat.id, response)
        return

    state = user_state.get(user_id, {})
    if state.get("view") == "was":
        show_was(call.message.chat.id, user_id, call.message.message_id)
    elif state.get("view") == "favorites":
        show_favorites(call.message.chat.id, user_id, call.message.message_id)
    else:
        show_place(call.message.chat.id, user_id, call.message.message_id)


# Функцияm ответа на комментарий
def process_comment_step(message, place_id):
    user_text = message.text
    contains_profanity, sentiment_score = analyze_komm(user_text)

    if contains_profanity:
        bot.send_message(
            message.chat.id,
            "Ваш комментарий содержит недопустимый контент и не может быть сохранен.",
        )
    else:
        add_comment_to_db(
            place_id, message.from_user.id, user_text, sentiment_score
        )
        bot.send_message(message.chat.id, "Ваш комментарий успешно добавлен!")


# Функция обработки оценки
def process_rating(message, place_id):
    try:
        score = int(message.text)
        if 0 <= score <= 10:
            rate_place(message.from_user.id, place_id, score)
            bot.send_message(message.chat.id, "Спасибо за вашу оценку!")
        else:
            bot.send_message(message.chat.id, "Введите число от 0 до 10.")
    except:
        bot.send_message(
            message.chat.id, "Введите корректное число от 0 до 10."
        )


# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(non_stop=True)
