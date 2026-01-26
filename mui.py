import logging
import random
from telegram import Update, ReplyKeyboardMarkup
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
TOKEN = '8470427152:AAGFuDNNKYcXSJmgM_KgO2hTI1XoAVtB8OI'

# Банк слов и подсказок
WORD_BANK = {
    "кошка": ["мяукает", "ловит мышей", "пушистая"],
    "яблоко": ["фрукт", "растёт на дереве", "хрустящее"],
    "лампа": ["даёт свет", "стоит на столе", "включается в розетку"],
    "книга": ["в ней текст", "её читают", "имеет страницы"],
    "дождь": ["падает с неба", "мокрое явление", "делает лужи"],
    "часы": ["показывают время", "тикают", "на руке или на стене"],
    "собака": ["лает", "друг человека", "охраняет дом"],
    "молоко": ["белое", "пьют", "от коровы"],
    "солнце": ["светит днём", "греет", "на небе"],
    "дверь": ["открывается", "в доме", "имеет ручку"],
    "компас": ["указывает стороны света", "для ориентирования", "имеет стрелку"],
    "заяц": ["прыгает", "уши длинные", "живёт в лесу"],
    "молния": ["сверкает", "гроза", "электрический разряд"],
    "мост": ["пересекает реку", "по нему ходят", "из металла или дерева"],
    "печь": ["готовит еду", "даёт тепло", "в ней огонь"],
    "зеркало": ["отражает лицо", "висит на стене", "стеклянное"],
    "рюкзак": ["носят за спиной", "для вещей", "в поход"],
    "фонарь": ["светит в темноте", "ручной", "батарейки"],
    "карта": ["показывает местность", "для путешественников", "с масштабом"],
    "весы": ["измеряют вес", "бывают напольные", "в магазине"],
    "эхо": ["отзвук", "в горах", "повторение голоса"],
    "призрак": ["привидение", "прозрачный", "ночью"],
    "лабиринт": ["много ходов", "трудно выйти", "запутанная сеть"],
    "алмаз": ["драгоценный камень", "самый твёрдый", "блестит"],
    "комета": ["летит в космосе", "хвост из льда", "редкое явление"],
    "иллюзия": ["обман зрения", "не то, чем кажется", "фокус"],
    "эпиграф": ["цитата перед книгой", "краткая мысль", "в начале главы"],
    "резонатор": ["усиливает звук", "в музыкальных инструментах", "колеблется"],
    "аномалия": ["отклонение от нормы", "странное явление", "научный термин"],
    "симуляция": ["имитация реальности", "компьютерная модель", "тренировка"],
}

# Хранилище активных игр: chat_id → данные игры
games = {}



class GuessWordGame:
    def __init__(self, num_teams: int):
        self.num_teams = num_teams
        self.scores = {f"Команда {i}": 0 for i in range(1, num_teams + 1)}
        self.current_round = 0
        self.max_rounds = num_teams 
        self.word = ""
        self.hints = []

    def new_word(self):
        """Выбирает новое слово и подсказки"""
        word, hints = random.choice(list(WORD_BANK.items()))
        self.word = word
        self.hints = hints

    def check_answer(self, answer: str) -> tuple[bool, str]:
        if not answer:
            return False, "Введите ответ!"
        if answer.strip().lower() == self.word:
            return True, "+5 очков! Правильно!"
        else:
            return False, "-2 очка! Неверно!"



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🎯 Добро пожаловать в игру «Угадай слово»!\n\n"
        "Я буду давать подсказки, а вы — угадывать слово.\n"
        "Сколько команд будет играть? (4–10)"
    )
    # Инициализируем игру
    games[update.message.chat_id] = {"state": "awaiting_teams"}



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()

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

        # Переход к следующему раунду
        game.current_round += 1

        if game.current_round >= game.max_rounds:
            # Игра закончена — показываем итоги
            results = "\n".join([f"{team}: {score}" for team, score in game.scores.items()])
            games[chat_id]["state"] = "game_over"
            await update.message.reply_text(
                f"🎮 Игра завершена! Итоги:\n\n{results}\n\n"
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
