import telebot
import random
from db import TelegramDBService
from gpt_model import GPTModel


class Bot:
    def __init__(self,
                 api_key: str,
                 tg_db: TelegramDBService,
                 gpt: GPTModel,
                 bot_names: list,
                 myaws_stickers: list,
                 bot_admins: str):
        self.bot = telebot.TeleBot(api_key)
        self.bot.message_handler(commands=['help', 'start'])(self.send_welcome)
        self.bot.message_handler(commands=['settings'])(self.update_setting)
        self.bot.message_handler(commands=['get_value'])(self.get_value)
        self.bot.message_handler(commands=['get_settings'])(self.get_settings)
        self.bot.message_handler(func=lambda message: True)(self.answer)
        self.tg_db = tg_db
        self.gpt = gpt
        self.bot_names = bot_names
        self.myaws_stickers = myaws_stickers
        self.sticker_probability = lambda: self.tg_db.get_settings()['sticker_probability']
        self.message_response_probability = lambda: self.tg_db.get_settings()['message_response_probability']
        self.response_probability = lambda: self.tg_db.get_settings()['response_probability']
        self.max_tokens = lambda: self.tg_db.get_settings()['max_tokens']
        self.bot_admins = bot_admins


    def check_user(func):
        def wrapper(self, message, *args, **kwargs):
            user_id = str(message.from_user.id)
            if user_id not in self.bot_admins:
                self.bot.reply_to(message, f"Блин хз, мое любимое число {user_id}")
                return
            return func(self, message, *args, **kwargs)
        return wrapper

    def run(self):
        self.bot.infinity_polling()

    @check_user
    def update_setting(self, message):
        try:
            parts = message.text.split(" ")
            if len(parts) < 3:
                raise ValueError("Недостаточно аргументов для обновления настройки.")
            var = parts[1]
            val = " ".join(parts[2:])
            val = int(val) if val.isdigit() else val
            self.tg_db.update_settings(**{var: val})
            self.bot.reply_to(message, f'Ну ок {var}')
            if var == 'system_context':
                self.gpt.system_context = val
        except Exception as e:
            self.bot.reply_to(message, f'Блин хз: {e}')

    @check_user
    def get_value(self, message):
        try:
            parts = message.text.split(" ")
            if len(parts) < 2:
                raise ValueError("Недостаточно аргументов для получения значения настройки.")
            var = parts[1]
            settings = self.tg_db.get_settings()
            if var not in settings:
                raise KeyError(f'Настройка "{var}" не найдена.')
            value = settings[var]
            self.bot.reply_to(message, f'{value}')
        except Exception as e:
            self.bot.reply_to(message, f'Блин хз: {e}')

    @check_user
    def get_settings(self, message):
        try:
            settings = "\n".join([f"{key}: <code>{value}</code>" for key, value in self.tg_db.get_settings().items()])
            self.bot.reply_to(message, settings, parse_mode='HTML')
        except Exception as e:
            self.bot.reply_to(message, f'хз блин: {e}')

    @check_user
    def send_welcome(self, message):
        self.bot.reply_to(message, text='/help \n'
                                        '/settings \n'
                                        '/get_value \n'
                                        '/get_settings \n')

    def answer(self, message):
        self._save_message(message)

        self._send_or_no(message)

    def _send_or_no(self,
                    message):
        if message.reply_to_message is not None and \
                message.reply_to_message.from_user.username in self.bot_names or \
                random.random() <= self.response_probability() or \
                any(keyword in message.text.lower() for keyword in self.bot_names):

            conversation = self._get_messages(message.chat.id)
            answer = self.gpt.conversation_generate_answer(conversation,
                                                           max_tokens=self.max_tokens())
            if random.random() <= self.message_response_probability():
                sent_message = self.bot.reply_to(message, answer)
            else:
                sent_message = self.bot.send_message(message.chat.id, answer)
            self._save_message(sent_message,)

        elif random.random() <= self.sticker_probability():
            sticker = random.choices(self.myaws_stickers)[0]
            self.bot.send_sticker(chat_id=message.chat.id, sticker=sticker)

    def _save_message(self,
                      message):
        self.tg_db.add_message(chat_id=message.chat.id,
                               user_id=message.from_user.id,
                               username=message.from_user.username,
                               message=message.text,
                               real_name=message.from_user.full_name)

    def _get_messages(self,
                      chat_id: int) -> list:
        history = self.tg_db.get_messages(chat_id, 20)

        formatted_messages = []
        for message in history:
            if message["username"] in self.bot_names:
                formatted_message = {'role': 'assistant','content': message["message"]}
            else:
                formatted_message = {'role': 'user', 'content': f'{message["real_name"]}: {message["message"]}'}

            formatted_messages.append(formatted_message)

        return formatted_messages
