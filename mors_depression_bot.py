import csv
import json
import os
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler


from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "7514034246:AAE3GPNYMc2UYoELxTagrYWeICz4S_Pbzzw"

CSV_FILE = "mors_weekly_data.csv"
USERS_FILE = "mors_users.json"

# ---------------------------------------------------
# Шкала депрессии Бека – BDI-II (русская версия)
# В пункте 9 убери звёздочки вручную!
# ---------------------------------------------------

BDI_ITEMS = [
    [
        "Я не чувствую себя расстроенным, печальным.",
        "Я расстроен.",
        "Я все время расстроен и не могу от этого отключиться.",
        "Я настолько расстроен и несчастлив, что не могу это выдержать."
    ],
    [
        "Я не тревожусь о своем будущем.",
        "Я чувствую, что озадачен будущим.",
        "Я чувствую, что меня ничего не ждёт.",
        "Моё будущее безнадёжно, и ничто не может измениться к лучшему."
    ],
    [
        "Я не чувствую себя неудачником.",
        "Я чувствую, что терпел больше неудач, чем другие.",
        "Когда я оглядываюсь на свою жизнь, я вижу много неудач.",
        "Я чувствую, что как личность я — полный неудачник."
    ],
    [
        "Я получаю столько же удовлетворения от жизни, как раньше.",
        "Я не получаю столько же удовлетворения, как раньше.",
        "Я больше не получаю удовольствия ни от чего.",
        "Я полностью не удовлетворён жизнью, и мне всё надоело."
    ],
    [
        "Я не чувствую себя виноватым.",
        "Я часто чувствую себя виноватым.",
        "Большую часть времени я чувствую себя виноватым.",
        "Я постоянно испытываю чувство вины."
    ],
    [
        "Я не чувствую, что могу быть наказан за что-либо.",
        "Я чувствую, что могу быть наказан.",
        "Я ожидаю, что могу быть наказан.",
        "Я чувствую себя уже наказанным."
    ],
    [
        "Я не разочаровался в себе.",
        "Я разочаровался в себе.",
        "Я себе противен.",
        "Я себя ненавижу."
    ],
    [
        "Я не хуже других.",
        "Я критикую себя за ошибки и слабости.",
        "Я всё время обвиняю себя за свои поступки.",
        "Я виню себя во всём плохом."
    ],
    [
        # !!! ПОСЛЕ КОПИРОВАНИЯ УБРАТЬ ЗВЁЗДОЧКИ !!!
        "Я никогда не думал покончить с собой.",
        "Иногда мелькают мысли о том, чтобы меня не было, но я не сделаю этого.",
        "Я хотел бы, чтобы всё закончилось.",
        "Я бы сделал себе вред, если бы представился случай."
    ],
    [
        "Я плачу не больше, чем обычно.",
        "Сейчас я плачу чаще.",
        "Теперь я всё время плачу.",
        "Раньше я мог плакать, а сейчас не могу, даже если хочу."
    ],
    [
        "Сейчас я раздражителен не более обычного.",
        "Я легче раздражаюсь, чем раньше.",
        "Теперь я постоянно чувствую раздражение.",
        "Я стал равнодушен к тому, что раньше раздражало."
    ],
    [
        "Я не утратил интерес к людям.",
        "Я меньше интересуюсь людьми, чем раньше.",
        "Я почти потерял интерес к людям.",
        "Я полностью утратил интерес к людям."
    ],
    [
        "Я откладываю принятие решений иногда, как раньше.",
        "Я чаще откладываю принятие решений.",
        "Мне труднее принимать решения.",
        "Я больше не могу принимать решения."
    ],
    [
        "Я не чувствую, что выгляжу хуже, чем обычно.",
        "Меня тревожит, что я выгляжу старым/непривлекательным.",
        "Я знаю, что изменения сделали меня непривлекательным.",
        "Я знаю, что выгляжу плохо."
    ],
    [
        "Я могу работать так же хорошо, как раньше.",
        "Мне нужно приложить усилие, чтобы начать.",
        "Я с трудом заставляю себя что-либо делать.",
        "Я совсем не могу работать."
    ],
    [
        "Я сплю так же хорошо, как раньше.",
        "Сейчас я сплю хуже.",
        "Я просыпаюсь раньше и мне трудно заснуть.",
        "Я просыпаюсь очень рано и больше не могу заснуть."
    ],
    [
        "Я устаю не больше обычного.",
        "Я устаю быстрее.",
        "Я устаю почти от всего.",
        "Я не могу ничего делать из-за усталости."
    ],
    [
        "Аппетит обычный.",
        "Аппетит хуже, чем раньше.",
        "Аппетит значительно хуже.",
        "Аппетита нет совсем."
    ],
    [
        "Я не похудел значительно.",
        "Я потерял более 2 кг.",
        "Я потерял более 5 кг.",
        "Я потерял более 7 кг."
    ],
    [
        "Я беспокоюсь о здоровье не больше обычного.",
        "Меня тревожат физические симптомы.",
        "Я очень обеспокоен состоянием.",
        "Я настолько обеспокоен, что не могу думать ни о чём другом."
    ],
    [
        "Интерес к сексу не изменился.",
        "Интерес слегка уменьшился.",
        "Интерес значительно уменьшился.",
        "Интерес полностью исчез."
    ]
]


# ---------------------------------------------------
# Работа с возрастом
# ---------------------------------------------------

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(d):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------
# CSV HEADER
# ---------------------------------------------------

def ensure_csv_header():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            header = [
                "user_id","age","date",
                "general_feeling",
                "pitrms_missed","pitrms_satisfaction",
                "ad_status","ad_effect",
            ]
            header += [f"bdi_{i}" for i in range(1, 22)]
            header += ["bdi_full","bdi_affective"]
            w.writerow(header)


# ---------------------------------------------------
# Клавиатуры
# ---------------------------------------------------

def scale_0_10(prefix):
    rows, row = [], []
    for i in range(0, 11):
        row.append(InlineKeyboardButton(str(i), callback_data=f"{prefix}_{i}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def kb_pitrms():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не пропускал(а)", callback_data="pitrms_none")],
        [InlineKeyboardButton("По забывчивости", callback_data="pitrms_forget")],
        [InlineKeyboardButton("Из-за побочных эффектов", callback_data="pitrms_sidefx")],
        [InlineKeyboardButton("Не было возможности", callback_data="pitrms_noaccess")],
        [InlineKeyboardButton("ПИТРС не был запланирован", callback_data="pitrms_notplanned")],
    ])


def kb_ad_status():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, по назначению врача МОРС", callback_data="ad_yes_mors")],
        [InlineKeyboardButton("Да, другой специалист", callback_data="ad_yes_other")],
        [InlineKeyboardButton("Нет", callback_data="ad_no")],
    ])


def kb_ad_effect():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Хорошо помогает", callback_data="adeff_good")],
        [InlineKeyboardButton("Немного помогает", callback_data="adeff_little")],
        [InlineKeyboardButton("Не помогает", callback_data="adeff_none")],
        [InlineKeyboardButton("Пока рано судить", callback_data="adeff_early")],
    ])


def kb_bdi_item(i):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("0", callback_data=f"bdi_{i}_0"),
        InlineKeyboardButton("1", callback_data=f"bdi_{i}_1"),
        InlineKeyboardButton("2", callback_data=f"bdi_{i}_2"),
        InlineKeyboardButton("3", callback_data=f"bdi_{i}_3"),
    ]])


# ---------------------------------------------------
# Переходы между вопросами
# ---------------------------------------------------

async def ask_general_feeling(chat_id, ctx):
    ctx.user_data["step"] = "general_feeling"
    await ctx.bot.send_message(
        chat_id,
        "Как вы себя чувствовали на этой неделе?\n(0 — очень плохо, 10 — отлично)",
        reply_markup=scale_0_10("feel")
    )


async def ask_pitrms(chat_id, ctx):
    ctx.user_data["step"] = "pitrms"
    await ctx.bot.send_message(chat_id, "Пропускали ли вы ПИТРС на этой неделе?",
                               reply_markup=kb_pitrms())


async def ask_pitrms_satisfaction(chat_id, ctx):
    ctx.user_data["step"] = "pitrms_satisfaction"
    await ctx.bot.send_message(
        chat_id,
        "Насколько вы удовлетворены терапией ПИТРС?\n(0 — совсем не удовлетворён(на), 10 — полностью)",
        reply_markup=scale_0_10("satp")
    )


async def ask_ad_status(chat_id, ctx):
    ctx.user_data["step"] = "ad_status"
    await ctx.bot.send_message(chat_id,
        "Под антидепрессантами мы имеем в виду СИОЗС/СИОЗСН.\n"
        "НЕ считаются: атаракс, новопассит, глицин, пустырник, тералиджен, грандаксин, фенибут и др."
    )
    await ctx.bot.send_message(chat_id,
        "Принимаете ли вы сейчас антидепрессант?",
        reply_markup=kb_ad_status()
    )


async def ask_ad_effect(chat_id, ctx):
    ctx.user_data["step"] = "ad_effect"
    await ctx.bot.send_message(chat_id, "Как вы оцениваете его эффект?",
                               reply_markup=kb_ad_effect())


async def ask_bdi_intro(chat_id, ctx):
    ctx.user_data["step"] = "bdi_intro"
    await ctx.bot.send_message(
        chat_id,
        "Далее идут вопросы шкалы депрессии Бека.\n"
        "Выберите утверждение, которое лучше всего описывает ваше состояние НА ЭТОЙ НЕДЕЛЕ."
    )
    await ask_bdi_item(chat_id, ctx, 1)


async def ask_bdi_item(chat_id, ctx, index):
    ctx.user_data["step"] = "bdi"
    ctx.user_data["bdi_index"] = index

    options = BDI_ITEMS[index - 1]
    text = f"{index}.\n" + "\n".join([f"{i} — {options[i]}" for i in range(4)])

    await ctx.bot.send_message(chat_id, text, reply_markup=kb_bdi_item(index))


# ---------------------------------------------------
# Старт бота
# ---------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    context.user_data.clear()
    context.user_data["user_id"] = uid

    users = load_users()
    age = users.get(str(uid))

    await update.message.reply_text("Здравствуйте! Это еженедельный опрос МОРС 😊")

    if age is None:
        context.user_data["step"] = "age"
        await update.message.reply_text("Пожалуйста, укажите ваш возраст (числом).")
    else:
        context.user_data["age"] = age
        await ask_general_feeling(chat_id, context)


# ---------------------------------------------------
# Обработка возраста
# ---------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "age":
        return

    txt = update.message.text.strip()
    if not txt.isdigit():
        await update.message.reply_text("Введите возраст цифрами.")
        return

    age = int(txt)
    if age < 10 or age > 100:
        await update.message.reply_text("Возраст должен быть от 10 до 100.")
        return

    uid = update.effective_user.id
    users = load_users()
    users[str(uid)] = age
    save_users(users)

    context.user_data["age"] = age
    await update.message.reply_text("Возраст сохранён!")

    chat_id = update.effective_chat.id
    await ask_general_feeling(chat_id, context)



# ---------------------------------------------------
# Callback handler
# ---------------------------------------------------

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    chat_id = q.message.chat.id
    await q.answer()

    step = context.user_data.get("step")

    if step == "general_feeling" and data.startswith("feel_"):
        context.user_data["general_feeling"] = int(data.split("_")[1])
        return await ask_pitrms(chat_id, context)

    if step == "pitrms" and data.startswith("pitrms_"):
        mapping = {
            "pitrms_none": "не пропускал(а)",
            "pitrms_forget": "по забывчивости",
            "pitrms_sidefx": "из-за побочных эффектов",
            "pitrms_noaccess": "не было возможности",
            "pitrms_notplanned": "ПИТРС не был запланирован",
        }
        context.user_data["pitrms_missed"] = mapping[data]
        return await ask_pitrms_satisfaction(chat_id, context)

    if step == "pitrms_satisfaction" and data.startswith("satp_"):
        context.user_data["pitrms_satisfaction"] = int(data.split("_")[1])
        return await ask_ad_status(chat_id, context)

    if step == "ad_status" and data.startswith("ad_"):
        mapping = {
            "ad_yes_mors": "МОРС",
            "ad_yes_other": "другой специалист",
            "ad_no": "нет",
        }
        context.user_data["ad_status"] = mapping[data]

        if data == "ad_no":
            context.user_data["ad_effect"] = ""
            return await ask_bdi_intro(chat_id, context)
        else:
            return await ask_ad_effect(chat_id, context)

    if step == "ad_effect" and data.startswith("adeff_"):
        mapping = {
            "adeff_good": "хорошо помогает",
            "adeff_little": "немного помогает",
            "adeff_none": "не помогает",
            "adeff_early": "пока рано судить",
        }
        context.user_data["ad_effect"] = mapping[data]
        return await ask_bdi_intro(chat_id, context)

    if step == "bdi" and data.startswith("bdi_"):
        _, idx, val = data.split("_")
        idx = int(idx)
        val = int(val)

        context.user_data.setdefault("bdi_scores", {})[idx] = val

        chosen_text = BDI_ITEMS[idx - 1][val]
        await q.message.reply_text(f"Вы выбрали:\n{val} — {chosen_text}")

        if idx < 21:
            return await ask_bdi_item(chat_id, context, idx + 1)
        else:
            return await save_and_finish(q, context)


# ---------------------------------------------------
# Сохранение результатов
# ---------------------------------------------------

async def save_and_finish(q, context):
    ensure_csv_header()

    uid = context.user_data.get("user_id")
    age = context.user_data.get("age")
    today = date.today().isoformat()

    bdi_scores = context.user_data.get("bdi_scores", {})
    bdi_list = [bdi_scores.get(i, "") for i in range(1, 22)]

    bdi_full = sum(int(x) for x in bdi_list if x != "")
    bdi_affective = sum(int(bdi_scores.get(i, 0)) for i in range(1, 14))

    row = [
        uid,
        age,
        today,
        context.user_data.get("general_feeling"),
        context.user_data.get("pitrms_missed"),
        context.user_data.get("pitrms_satisfaction"),
        context.user_data.get("ad_status"),
        context.user_data.get("ad_effect"),
    ]

    row += bdi_list
    row += [bdi_full, bdi_affective]

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(row)

    await q.message.reply_text("Спасибо! Ваши ответы сохранены ❤️")
    context.user_data.clear()

async def weekly_broadcast(app):
    """Рассылка /start всем зарегистрированным пользователям."""
    users = load_users()
    for uid in users.keys():
        try:
            await app.bot.send_message(chat_id=int(uid), text="/start")
        except Exception as e:
            print(f"Ошибка отправки пользователю {uid}: {e}")


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

def main():
    ensure_csv_header()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # --- APSCHEDULER: запуск по пятницам в 13:30 ---
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        weekly_broadcast,
        trigger="cron",
        day_of_week="fri",
        hour=13,
        minute=30,
        args=[app]
    )
    scheduler.start()
    # ------------------------------------------------

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
