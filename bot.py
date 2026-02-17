import logging
import random

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import database as db

BOT_TOKEN = "1465130142:AAG1Bk4vbL7ZkVzZJJnNukvuux5-q2Y26IQ"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Conversation states ─────────────────────────────────────────

(
    AUTH_CHOICE,
    REG_USERNAME,
    REG_PASSWORD,
    LOGIN_USERNAME,
    LOGIN_PASSWORD,
    MAIN_MENU,
    DIFFICULTY,
    PLAYING,
    HOW_TO_PLAY_MENU,
) = range(9)

# ── Keyboards ────────────────────────────────────────────────────

AUTH_KEYBOARD = ReplyKeyboardMarkup(
    [["Зарегистрироваться!", "Войти"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Профиль", "Расскажи как играть?", "Играть с ботом"],
        ["Выйти из аккаунта"],
    ],
    resize_keyboard=True,
)

DIFFICULTY_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Новичок", "Любитель"],
        ["Профессионал", "Бог игры"],
        ["Назад"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

HOW_TO_PLAY_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Расскажи правила", "Расскажи про уровни сложности"],
        ["Назад"],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

GAME_KEYBOARD = ReplyKeyboardMarkup(
    [["Сдаться"]],
    resize_keyboard=True,
)

# ── Difficulty settings ──────────────────────────────────────────

DIFFICULTIES = {
    "Новичок": 20,
    "Любитель": 15,
    "Профессионал": 12,
    "Бог игры": 8,
}

WELCOME_TEXT = (
    "Добро пожаловать в главное меню бота!\n"
    'Выберите "Профиль", чтобы узнать актуальную информацию о вас.\n'
    'Выберите "Расскажи как играть?", если вы новичек и хотите '
    "научиться хорошо играть.\n"
    'Выберите "Играть с ботом", если вы готовы к поединку с ботом!\n'
    'Выберите "Выйти из аккаунта", если хотите сменить аккаунт.'
)

# ── Helpers ──────────────────────────────────────────────────────


def generate_secret() -> str:
    digits = list(range(10))
    random.shuffle(digits)
    return "".join(str(d) for d in digits[:4])


def calculate_bulls_cows(secret: str, guess: str) -> tuple[int, int]:
    bulls = sum(s == g for s, g in zip(secret, guess))
    cows = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - bulls
    return bulls, cows


# ── /start ───────────────────────────────────────────────────────


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    telegram_id = update.effective_user.id

    user = db.get_logged_in_user(telegram_id)
    if user:
        await update.message.reply_text(
            f"С возвращением, {user['username']}! {WELCOME_TEXT}",
            reply_markup=MAIN_KEYBOARD,
        )
        return MAIN_MENU

    await update.message.reply_text(
        "Привет! Зарегистрируйся или войди в свой аккаунт, чтобы продолжить!",
        reply_markup=AUTH_KEYBOARD,
    )
    return AUTH_CHOICE


# ── Registration ─────────────────────────────────────────────────


async def auth_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Зарегистрироваться!":
        await update.message.reply_text(
            "Введите ваш логин:", reply_markup=ReplyKeyboardRemove()
        )
        return REG_USERNAME

    elif text == "Войти":
        await update.message.reply_text(
            "Введите ваш логин:", reply_markup=ReplyKeyboardRemove()
        )
        return LOGIN_USERNAME

    await update.message.reply_text(
        "Пожалуйста, выберите одну из кнопок.", reply_markup=AUTH_KEYBOARD
    )
    return AUTH_CHOICE


async def reg_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text.strip()

    if db.username_exists(username):
        await update.message.reply_text("Этот логин уже занят. Попробуйте другой:")
        return REG_USERNAME

    context.user_data["reg_username"] = username
    await update.message.reply_text("Введите пароль:")
    return REG_PASSWORD


async def reg_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    username = context.user_data["reg_username"]
    telegram_id = update.effective_user.id

    if db.register_user(telegram_id, username, password):
        await update.message.reply_text(
            f"Отлично, вы успешно зарегистрировались! {WELCOME_TEXT}",
            reply_markup=MAIN_KEYBOARD,
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Не удалось зарегистрироваться. Попробуйте снова.",
            reply_markup=AUTH_KEYBOARD,
        )
        return AUTH_CHOICE


# ── Login ────────────────────────────────────────────────────────


async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["login_username"] = update.message.text.strip()
    await update.message.reply_text("Введите пароль:")
    return LOGIN_PASSWORD


async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    username = context.user_data["login_username"]
    telegram_id = update.effective_user.id

    user = db.login_user(username, password)
    if user:
        if user["telegram_id"] != telegram_id:
            await update.message.reply_text(
                "Этот аккаунт привязан к другому Telegram. Попробуйте другой логин.",
                reply_markup=AUTH_KEYBOARD,
            )
            return AUTH_CHOICE

        db.set_logged_in(telegram_id)
        await update.message.reply_text(
            f"Отлично, вы успешно вошли в свой аккаунт! {WELCOME_TEXT}",
            reply_markup=MAIN_KEYBOARD,
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Неверный логин или пароль. Попробуйте снова.\nВведите ваш логин:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return LOGIN_USERNAME


# ── Main menu ────────────────────────────────────────────────────


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Профиль":
        return await show_profile(update, context)

    elif text == "Расскажи как играть?":
        await update.message.reply_text(
            "Выберите что вас интересует:", reply_markup=HOW_TO_PLAY_KEYBOARD
        )
        return HOW_TO_PLAY_MENU

    elif text == "Играть с ботом":
        await update.message.reply_text(
            "Выберите уровень сложности:", reply_markup=DIFFICULTY_KEYBOARD
        )
        return DIFFICULTY

    elif text == "Выйти из аккаунта":
        telegram_id = update.effective_user.id
        db.logout_user(telegram_id)
        context.user_data.clear()
        await update.message.reply_text(
            "Вы вышли из аккаунта. До встречи! 👋\n"
            "Нажмите /start, чтобы войти снова.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    await update.message.reply_text("Вы в главном меню!", reply_markup=MAIN_KEYBOARD)
    return MAIN_MENU


# ── Profile ──────────────────────────────────────────────────────


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = db.get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "Не удалось найти профиль.", reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU

    win_rate = (
        f"{user['games_won'] / user['games_played'] * 100:.1f}%"
        if user["games_played"] > 0
        else "—"
    )

    text = (
        f"📋 *Ваш профиль*\n\n"
        f"👤 Логин: `{user['username']}`\n"
        f"🎮 Игр сыграно: {user['games_played']}\n"
        f"🏆 Побед: {user['games_won']}\n"
        f"📊 Процент побед: {win_rate}\n"
        f"📅 Дата регистрации: {user['created_at']}"
    )

    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD
    )
    return MAIN_MENU


# ── How to play ──────────────────────────────────────────────────


async def how_to_play_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Расскажи правила":
        rules = (
            "Компьютер задумывает четыре различные цифры из 0,1,2…9.\n"
            "Игрок делает ходы, чтобы узнать эти цифры и их порядок.\n"
            "Каждый ход состоит из четырёх цифр. 0 может стоять на первом месте.\n"
            "В ответ компьютер показывает число отгаданных цифр, "
            "стоящих на своих местах (число быков) и число отгаданных цифр, "
            "стоящих не на своих местах (число коров).\n\n"
            "Пример:\n"
            "Компьютер задумал 0834.\n"
            "Игрок сделал ход 8134.\n"
            "Компьютер ответил: 2 быка (3 и 4) и 1 корова (8).\n\n"
            "Цель — угадать все 4 цифры и их позиции за отведённое число попыток!"
        )
        await update.message.reply_text(rules, reply_markup=HOW_TO_PLAY_KEYBOARD)
        return HOW_TO_PLAY_MENU

    elif text == "Расскажи про уровни сложности":
        levels = (
            "🎯 *Уровни сложности:*\n\n"
            "🟢 *Новичок* — 20 попыток\n"
            "🟡 *Любитель* — 15 попыток\n"
            "🟠 *Профессионал* — 12 попыток\n"
            "🔴 *Бог игры* — 8 попыток"
        )
        await update.message.reply_text(
            levels, parse_mode="Markdown", reply_markup=HOW_TO_PLAY_KEYBOARD
        )
        return HOW_TO_PLAY_MENU

    elif text == "Назад":
        await update.message.reply_text(
            "Вы в главном меню!", reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU

    await update.message.reply_text(
        "Выберите что вас интересует:", reply_markup=HOW_TO_PLAY_KEYBOARD
    )
    return HOW_TO_PLAY_MENU


# ── Difficulty / game start ──────────────────────────────────────


async def choose_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Назад":
        await update.message.reply_text(
            "Вы в главном меню!", reply_markup=MAIN_KEYBOARD
        )
        return MAIN_MENU

    if text not in DIFFICULTIES:
        await update.message.reply_text(
            "Пожалуйста, выберите уровень сложности из списка.",
            reply_markup=DIFFICULTY_KEYBOARD,
        )
        return DIFFICULTY

    max_attempts = DIFFICULTIES[text]
    secret = generate_secret()
    user = db.get_user(update.effective_user.id)

    game_id = db.create_game(user["id"], secret, max_attempts, text)
    context.user_data["game_id"] = game_id
    context.user_data["secret"] = secret
    context.user_data["attempts_left"] = max_attempts
    context.user_data["max_attempts"] = max_attempts
    context.user_data["user_db_id"] = user["id"]

    await update.message.reply_text(
        f"Я загадал число, у вас есть {max_attempts} попыток, "
        f"чтобы его угадать.\nНапишите ваше число:",
        reply_markup=GAME_KEYBOARD,
    )
    return PLAYING


# ── Gameplay ─────────────────────────────────────────────────────


async def play_turn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    if text == "Сдаться":
        game_id = context.user_data.get("game_id")
        user_db_id = context.user_data.get("user_db_id")
        secret = context.user_data.get("secret")
        if game_id:
            db.end_game(game_id)
            db.increment_games_played(user_db_id)
        await update.message.reply_text(
            f"Вы сдались! Загаданное число было: {secret}.\n"
            f"Не расстраивайтесь, в следующий раз повезёт! 💪",
            reply_markup=MAIN_KEYBOARD,
        )
        return MAIN_MENU

    if len(text) != 4 or not text.isdigit() or len(set(text)) != 4:
        await update.message.reply_text(
            "Введите ровно 4 *различные* цифры (0-9).\nПопробуйте ещё раз:",
            parse_mode="Markdown",
            reply_markup=GAME_KEYBOARD,
        )
        return PLAYING

    secret = context.user_data["secret"]
    bulls, cows = calculate_bulls_cows(secret, text)

    context.user_data["attempts_left"] -= 1
    db.decrement_attempts(context.user_data["game_id"])
    attempts_left = context.user_data["attempts_left"]
    attempts_used = context.user_data["max_attempts"] - attempts_left

    if bulls == 4:
        db.end_game(context.user_data["game_id"])
        db.increment_games_played(context.user_data["user_db_id"])
        db.increment_games_won(context.user_data["user_db_id"])

        await update.message.reply_text(
            f"🎉 Вы угадали! Отличная игра! "
            f"Вам потребовалось {attempts_used} "
            f"попыт{'ка' if attempts_used == 1 else 'ок' if attempts_used >= 5 else 'ки'} "
            f"для того чтобы угадать.",
            reply_markup=MAIN_KEYBOARD,
        )
        return MAIN_MENU

    if attempts_left <= 0:
        db.end_game(context.user_data["game_id"])
        db.increment_games_played(context.user_data["user_db_id"])

        await update.message.reply_text(
            f"😔 Попытки закончились! Загаданное число было: {secret}.\n"
            f"Не расстраивайтесь, попробуйте ещё раз!",
            reply_markup=MAIN_KEYBOARD,
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"🐂 Быков: {bulls}  |  🐄 Коров: {cows}\n"
        f"Осталось попыток: {attempts_left}\n"
        f"Напишите ваше число:",
        reply_markup=GAME_KEYBOARD,
    )
    return PLAYING


# ── Cancel ───────────────────────────────────────────────────────


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено. Нажмите /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── Main ─────────────────────────────────────────────────────────


def main():
    db.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTH_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, auth_choice)],
            REG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_username)],
            REG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_password)],
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            DIFFICULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_difficulty)],
            PLAYING: [MessageHandler(filters.TEXT & ~filters.COMMAND, play_turn)],
            HOW_TO_PLAY_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, how_to_play_menu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    logger.info("Bot started! Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
