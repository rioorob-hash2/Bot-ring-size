import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Замените 'YOUR_TOKEN' на токен, который вам выдал BotFather
TOKEN = "8239256102:AAG9aLPJwR4zDG-RWt0XY-obFm1HcpPdqoU"

# Определяем состояния для ConversationHandler
PURITY, PROFILE, WIDTH, HEIGHT, SIZE = range(5)

# Устанавливаем базовую конфигурацию логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

def get_keyboard_with_restart():
    """Создает клавиатуру с кнопкой "Начать сначала"."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("Начать сначала", callback_data="restart")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет приветственное сообщение и предлагает выбрать пробу золота."""
    keyboard = [
        [
            InlineKeyboardButton("Золото 585", callback_data="585"),
            InlineKeyboardButton("Золото 750", callback_data="750"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я помогу рассчитать вес кольца. Выберите пробу золота:", reply_markup=reply_markup
    )
    return PURITY

async def select_purity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор пробы и просит выбрать профиль."""
    query = update.callback_query
    await query.answer()

    purity = query.data
    context.user_data['purity'] = purity

    keyboard = [
        [
            InlineKeyboardButton("Прямоугольный", callback_data="Прямоугольный"),
            InlineKeyboardButton("Полукруглый", callback_data="Полукруглый"),
        ],
        [InlineKeyboardButton("Начать сначала", callback_data="restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Вы выбрали золото **{purity}**. Теперь выберите профиль кольца:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return PROFILE

async def select_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор профиля и просит ввести ширину."""
    query = update.callback_query
    await query.answer()

    profile = query.data
    context.user_data['profile'] = profile

    await query.edit_message_text(
        f"Вы выбрали профиль: **{profile}**\n\nВведите ширину кольца в мм:",
        reply_markup=get_keyboard_with_restart(),
        parse_mode="Markdown",
    )
    return WIDTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает ширину и просит ввести высоту."""
    try:
        width = float(update.message.text.replace(',', '.'))
        context.user_data['width'] = width
        await update.message.reply_text(
            "Ширина принята. Теперь введите высоту профиля в мм:", reply_markup=get_keyboard_with_restart()
        )
        return HEIGHT
    except (ValueError, TypeError):
        await update.message.reply_text("Пожалуйста, введите число.")
        return WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает высоту и просит ввести размер."""
    try:
        height = float(update.message.text.replace(',', '.'))
        context.user_data['height'] = height
        await update.message.reply_text(
            "Высота принята. Теперь введите размер кольца (например, 18):", reply_markup=get_keyboard_with_restart()
        )
        return SIZE
    except (ValueError, TypeError):
        await update.message.reply_text("Пожалуйста, введите число.")
        return HEIGHT

async def get_size_and_calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает размер, выполняет расчет и выводит результат."""
    try:
        size = float(update.message.text.replace(',', '.'))
        context.user_data['size'] = size
    except (ValueError, TypeError):
        await update.message.reply_text("Пожалуйста, введите число.")
        return SIZE

    # Получаем все данные из контекста пользователя
    purity = context.user_data['purity']
    profile = context.user_data['profile']
    width = context.user_data['width']
    height = context.user_data['height']

    # Определяем плотность в зависимости от пробы
    if purity == "585":
        density = 0.0135  # 13.5 г/см³ = 0.0135 г/мм³
    elif purity == "750":
        density = 0.0152  # 15.2 г/см³ = 0.0152 г/мм³
    else:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте начать сначала командой /start."
        )
        return ConversationHandler.END

    pi = 3.14159

    if profile == "Прямоугольный":
        area = width * height
    elif profile == "Полукруглый":
        area = (width * height) + (pi * (width / 2)**2) / 2

    # Расчет объема и веса
    length = size * pi
    volume = area * length
    weight = volume * density

    await update.message.reply_text(
        f"Проба: **Золото {purity}**\n"
        f"Профиль: **{profile}**\n"
        f"Ширина: {width} мм\n"
        f"Высота: {height} мм\n"
        f"Размер: {size}\n"
        f"---"
        f"**Расчетный вес кольца:** {weight:.2f} г.",
        parse_mode="Markdown",
        reply_markup=get_keyboard_with_restart(),
    )

    # Важно: Не завершаем диалог, чтобы кнопка "Начать сначала" продолжала работать.
    # В этом случае, если пользователь нажмет на кнопку, будет вызван обработчик restart_conversation.
    # Если же он введет какой-либо текст, бот просто будет ждать команды.
    return SIZE

async def restart_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает нажатие кнопки "Начать сначала"."""
    query = update.callback_query
    await query.answer()
    
    # Очищаем данные пользователя и перезапускаем диалог
    context.user_data.clear()
    
    keyboard = [
        [
            InlineKeyboardButton("Золото 585", callback_data="585"),
            InlineKeyboardButton("Золото 750", callback_data="750"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Меняем сообщение, чтобы начать заново
    await query.edit_message_text(
        "Начинаем сначала. Выберите пробу золота:", reply_markup=reply_markup
    )
    return PURITY

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершает диалог."""
    await update.message.reply_text("Расчет отменен. Чтобы начать снова, введите /start.")
    return ConversationHandler.END

def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PURITY: [
                CallbackQueryHandler(select_purity, pattern="^(585|750)$"),
            ],
            PROFILE: [
                CallbackQueryHandler(select_profile, pattern="^(Прямоугольный|Полукруглый)$"),
            ],
            WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_size_and_calculate)],
        },
        fallbacks=[
            CallbackQueryHandler(restart_conversation, pattern="^restart$"),
            CommandHandler("cancel", cancel)
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()