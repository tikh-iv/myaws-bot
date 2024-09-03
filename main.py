import os
from bot import Bot
from db import TelegramDBService
from gpt_model import GPTModel


class Configs:
    def __init__(self):
        self.telegram_api_token = os.getenv('TELEGRAM_API_TOKEN', 'default_api_key')
        self.db_name = os.getenv('DB_NAME', 'sqlite:///telegram_bot.sqlite')
        self.base_url = os.getenv('BASE_URL', 'https://openrouter.ai/api/v1')
        self.gpt_api_key = os.getenv('GPT_API_KEY', 'default_api_key')
        self.model = os.getenv('MODEL', 'openai/gpt-4o-mini')
        self.system_context_file = os.getenv('SYSTEM_CONTEXT', '')
        self.bot_names = os.getenv('BOT_NAMES', 'MeowSavbot,pawnpaw').split(',')
        self.bot_admins = os.getenv('bot_admin', '293754044').split(',')
        self.myaws_stickers = os.getenv('MYAWS_STICKERS', 'CAACAgIAAxkBAAJxnmbS7CjSaaLcOru8VQjMpCGKK8D2AALsLgACIR2RSjze-Kvp7EqqNQQ,'
                                                          'CAACAgIAAxkBAAJxoWbS7QJxGh1orFVDYG98rdgedaQdAAKtIgACMLyZSPK5-lHyC_4ONQQ,'
                                                          'CAACAgIAAxkBAAJxpGbS7RSEIo-oSq_PLeZc_gQ59OaNAAJhIwAC0onxSAdgKmaBpct4NQQ,'
                                                          'CAACAgIAAxkBAAJxp2bS7SFIN03GCx-fwmfrEneBgQVBAALPPgACfkfwSMBh8Zf6fDGsNQQ'.split(','))

        if os.path.exists(self.system_context_file):
            with open(self.system_context_file, 'r') as f:
                self.system_context = f.read()
        else:
            self.system_context = ''



if __name__ == '__main__':
    configs = Configs()

    tg_db = TelegramDBService(db_name=configs.db_name)

    # Если контекст по умолчанию пустой берем его из таблицы настроек, если не пустой обновляем БД
    if configs.system_context:
        configs.system_context = tg_db.get_settings()['system_context']
    else:
        tg_db.update_settings(system_context=configs.system_context)

    gpt = GPTModel(base_url=configs.base_url,
                   gpt_api_key=configs.gpt_api_key,
                   system_context=configs.system_context,
                   model=configs.model)

    bot = Bot(api_key=configs.telegram_api_token,
              tg_db=tg_db,
              gpt=gpt,
              bot_names=configs.bot_names,
              myaws_stickers=configs.myaws_stickers,
              bot_admins=configs.bot_admins)
    bot.run()