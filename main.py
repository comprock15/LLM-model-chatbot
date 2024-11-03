import telebot
import requests
import jsons
import json
import os
from Class_ModelResponse import ModelResponse

# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
token_filename = 'API_TOKEN.txt'
with open(token_filename) as f:
    API_TOKEN = f.readline()
bot = telebot.TeleBot(API_TOKEN)
chat_history_folder = 'chat_history'


def set_commands():
    c1 = telebot.types.BotCommand(command='start', description='Вывод всех доступных команд')
    c2 = telebot.types.BotCommand(command='model', description='Вывод названия используемой языковой модели')
    c3 = telebot.types.BotCommand(command='clear', description='Очистка контекста')
    bot.set_my_commands([c1, c2, c3])


# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Эм... Привет, я Скибиду. Кажется, я понимаю такие команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - вывод названия используемой языковой модели\n"
        "/clear - очистка контекста\n"
        "Отправь мне сообщение, и, возможно, я на него отвечу..."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    history_json = os.path.join(chat_history_folder, str(message.chat.id) + ".json")
    # Очищаем историю
    if os.path.exists(history_json):
        os.remove(history_json)
    bot.reply_to(message, 'Контекст очищен.')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, 'Дайте подумать...')

    user_query = message.text
    history_json = os.path.join(chat_history_folder, str(message.chat.id) + ".json")

    history = []

    # Загрузка истории сообщений
    if os.path.exists(history_json):
        with open(history_json) as f:
            history = json.load(f)

    history.append(
        {
            "role": "user",
            "content": user_query
        }
    )
    request = {
        "messages": history
    }
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    bot.delete_message(message.chat.id, message.message_id + 1)
    if response.status_code == 200:
        model_response :ModelResponse = jsons.loads(response.text, ModelResponse)
        bot.reply_to(message, model_response.choices[0].message.content)
        history.append(
            {
                "role": "assistant",
                "content": model_response.choices[0].message.content
            }
        )
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')

    with open(history_json, "w") as f:
        json.dump(history, f)


# Запуск бота
if __name__ == '__main__':
    if not os.path.exists(chat_history_folder):
        os.mkdir(chat_history_folder)
    #for f in os.listdir(chat_history_folder):
    #    os.remove(os.path.join(chat_history_folder, f))
    set_commands()
    bot.polling(none_stop=True)