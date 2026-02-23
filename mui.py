import logging
import random
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
TOKEN = '565656'

# ID администратора (замените на реальный ID)
YOUR_ADMIN_ID = 123456789  # Замените на ваш ID Telegram


# Банк слов, подсказок и синонимов
WORD_BANK = {
    "кошка": {
        "hints": ["мяукает", "ловит мышей", "пушистая"],
        "synonyms": ["кот", "котик", "кошечка", "котенок"]
    },
    "яблоко": {
        "hints": ["фрукт", "растёт на дереве", "хрустящее", "бывает красное, зеленое или желтое"],
        "synonyms": ["плод", "антоновка", "симиренко"]
    },
    "лампа": {
        "hints": ["даёт свет", "стоит на столе", "включается в розетку"],
        "synonyms": ["светильник", "подсвечник", "торшер"]
    },
    "книга": {
        "hints": ["в ней текст", "её читают", "имеет страницы"],
        "synonyms": ["книжечка", "том", "учебник"]
    },
    "дождь": {
        "hints": ["падает с неба", "мокрое явление", "делает лужи"],
        "synonyms": ["дождик", "ливень", "морось"]
    },
    "часы": {
        "hints": ["показывают время", "тикают", "на руке или на стене"],
        "synonyms": ["наручные часы", "будильник", "хронометр"]
    },
    "собака": {
        "hints": ["лает", "друг человека", "охраняет дом"],
        "synonyms": ["пёс", "щенок", "песик"]
    },
    "молоко": {
        "hints": ["белое", "пьют", "от коровы"],
        "synonyms": ["молочный продукт", "коровье молоко", "молочко"]
    },
    "солнце": {
        "hints": ["светит днём", "греет", "на небе"],
        "synonyms": ["светило", "сонце", "солнышко"]
    },
    "дверь": {
        "hints": ["открывается", "в доме", "имеет ручку"],
        "synonyms": ["входная дверь", "дверца", "калитка"]
    }
}

# Хранилище активных игр: chat_id → данные игры
games = {}

# Хранилище заблокированных пользователей (user_id)
banned_users = set()

class GuessWordGame:
    def __init__(self, num_teams: int):
        self.num_teams = num_teams
        self.scores = {f"Команда {i}": 0 for i in range(1, num_teams + 1)}
        self.current_round = 0
        self.max_rounds = 3*num_teams 
        self.word = ""
        self.hints = []
        self.synonyms = []

    def new_word(self):
        """Выбирает новое слово, подсказки и синонимы"""
        word_data = random.choice(list(WORD_BANK.items()))
        self.word = word_data[0]
        self.hints = word_data[1]["hints"]
        self.synonyms = word_data[1].get("synonyms", [])

    def check_answer(self, answer: str) -> tuple[bool, str]:
        if not answer:
            return False, "Введите ответ!"

        answer_clean = answer.strip().lower()
        # Проверяем основное слово и все синонимы
        if answer_clean == self.word or answer_clean in self.synonyms:
            return True, "+5 очков! Правильно!"
        else:
            return False, "-2 очка! Неверно!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🎯 Добро пожаловать в игру «Угадай слово»!\n\n"
        "Я буду давать подсказки, а вы — угадывать слово.\n"
        "Сколько команд будет играть? (1–10)"
    )
    # Инициализируем игру
    games[update.message.chat_id] = {"state": "awaiting_teams"}

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для блокировки пользователя (только для админов)"""
    user_id = update.message.from_user.id
    # Проверка прав администратора
    if user_id != YOUR_ADMIN_ID:
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /ban <user_id>")
        return

    try:
        target_id = int(context.args[0])
        banned_users.add(target_id)
        await update.message.reply_text(f"Пользователь {target_id} заблокирован.")
    except ValueError:
        await update.message.reply_text("Неверный формат ID.")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для разблокировки пользователя (только для админов)"""
    user_id = update.message.from_user.id
    if user_id != YOUR_ADMIN_ID:
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /unban <user_id>")
        return

    try:
        target_id = int(context.args[0])
        if target_id in banned_users:
            banned_users.remove(target_id)
            await update.message.reply_text(f"Пользователь {target_id} разблокирован.")
        else:
            await update.message.reply_text(f"Пользователь {target_id} не в списке заблокированных.")
    except ValueError:
        await update.message.reply_text("Неверный формат ID.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Проверка на блокировку
    if user_id in banned_users:
        await update.message.reply_text("Вы заблокированы и не можете участвовать в игре.")
        return

    # Если игры нет, просим начать с /start
    if chat_id not in games:
        await update.message.reply_text("Начните игру с /start")
        return

    game_data = games[chat_id]
    state = game_data["state"]

    # 1. Ожидание количества команд
    if state == "awaiting_teams":
        try:
            num_teams = int(text)
            if 1 <= num_teams <= 10:
                # Создаём игру
                game = GuessWordGame(num_teams)
                game.new_word()  # первое слово
                games[chat_id] = {
                    "game": game,
            "state": "playing",
            "current_team": 1,
                }
                await update.message.reply_text(
                    f"Игра началась! {game.max_rounds} раундов.\n"
            f"Команда 1, ваша подсказка:\n{', '.join(game.hints)}"
                )
            else:
                await update.message.reply_text("Введите число от 1 до 10.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число.")

    # 2. Игровой процесс
    elif state == "playing":
        game = game_data["game"]
        current_team = game_data["current_team"]
        team_name = f"Команда {current_team}"

        # Проверяем ответ
        is_correct, msg = game.check_answer(text)

        if is_correct:
            game.scores[team_name] += 5
            await update.message.reply_text(f"{msg} 🎯")
        else:
            game.scores[team_name] -= 2
            await update.message.reply_text(f"{msg} ❌")

        # Промежуточный отчёт после раунда (опционально)
        current_results = []
        sorted_current = sorted(
            game.scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for i, (team, score) in enumerate(sorted_current, 1):
            current_results.append(f"{i}. {team}: {score}")
        current_report = "\n".join(current_results)
        await update.message.reply_text(
            f"📝 ПРОМЕЖУТОЧНЫЕ РЕЗУЛЬТАТЫ:\n{current_report}\n"
        )

        # Переход к следующему раунду
        game.current_round += 1

        if game.current_round >= game.max_rounds:
            # Игра закончена — показываем итоги с подробным отчётом
            results = []
            sorted_scores = sorted(
                game.scores.items(),
                key=lambda x: x[1],
                reverse=True  # Сортируем по убыванию очков
            )
            for i, (team, score) in enumerate(sorted_scores, 1):
                if score >= 0:
                    results.append(f"{i}. {team}: {score} очков ✅")
                else:
                    results.append(f"{i}. {team}: {score} очков ❌")
            final_results = "\n".join(results)
            games[chat_id]["state"] = "game_over"
            await update.message.reply_text(
                f"🎮 ИГРА ЗАВЕРШЕНА! 🏁\n\n"
                f"🏆 ФИНАЛЬНЫЙ РЕЙТИНГ 🏆\n"
                f"{final_results}\n\n"
                f"🎉 Поздравляем победителей!\n\n"
                "Хотите сыграть ещё? (да/нет)"
            )
        else:
            # Следующая команда
            game_data["current_team"] = (current_team % game.num_teams) + 1
            game.new_word()  # новое слово
            next_team = game_data["current_team"]
            await update.message.reply_text(
                f"Раунд {game.current_round + 1}. Команда {next_team}, ваша подсказка:\n"
                f"{', '.join(game.hints)}"
            )
      # 3. Предложение новой игры
    elif state == "game_over":
        if text.lower() in ("да", "yes", "конечно", "давай"):
            # Перезапускаем игру
            num_teams = len(game_data["game"].scores)
            game = GuessWordGame(num_teams)
            game.new_word()
            games[chat_id] = {
                "game": game,
                "state": "playing",
                "current_team": 1,
            }
            await update.message.reply_text(
                f"Новая игра! {game.max_rounds} раундов.\n"
                f"Команда 1, подсказка:\n{', '.join(game.hints)}"
            )
        else:
            await update.message.reply_text("Спасибо за игру! До встречи! 👋")
            # Удаляем игру
            del games[chat_id]



def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен. Ожидание сообщений...")
    application.run_polling()



if __name__ == "__main__":
    main()      
