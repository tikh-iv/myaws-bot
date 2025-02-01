from openai import OpenAI
from image_yandex import ImageYandex
import json
import telebot


class GPTModel:
    def __init__(self,
                 base_url: str,
                 gpt_api_key: str,
                 system_context: str,
                 model: str,
                 image_yandex: ImageYandex,
                 bot: telebot.TeleBot = None):
        """
        Модель для работы с GPT
        :param base_url:
        :param gpt_api_key:
        :param system_context:
        :param model:
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=gpt_api_key,
        )
        self.system_context = system_context
        self.model = model
        self.image_yandex = image_yandex
        self.bot = bot
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_image",
                    "description": "Создает изображение на основании запроса",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Описание изображения"},
                            "width_ratio": {"type": "integer", "description": "width ratio"},
                            "height_ratio": {"type": "integer", "description": "height ratio"}
                        },
                        "required": ["Image"]
                    }
                }
            }
        ]


    def conversation_generate_answer(self,
                                     conversation: list,
                                     max_tokens: int = 100,
                                     message = None) -> str:
        messages = [{"role": "system", "content": self.system_context},]
        messages.extend(conversation)

        return self._generate_answer(messages, max_tokens, message)

    def _handle_tool_calls(self,
                           tool_call,
                           message: telebot.types.Message):
        """
        Обрабатывает вызовы инструментов (tool_calls) и выполняет соответствующие функции.
        """

        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "crate_image":
            try:
                image_bytes = self.image_yandex.create_image(
                    prompt=arguments["Image"],
                    width_ratio=arguments.get("width_ratio", 1),
                    height_ratio=arguments.get("height_ratio", 1)
                )
                self.bot.send_photo(chat_id=message.chat.id, photo=image_bytes, reply_to_message_id=message.message_id)
                return "Изображение создано"
            except Exception as e:
                pass
        return "Ошибка генерации"

    def _generate_answer(self,
                         messages: list,
                         max_tokens: int = 100,
                         message = None):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                tools=self.tools,
            )
        except Exception as e:
            return f"Блин, хз, а как решить проблему {e}"
        try:
            # Проверяем, есть ли tool_calls
            tool_calls = completion.choices[0].message.tool_calls if completion.choices else None

            if tool_calls:
                for tool_call in tool_calls:
                    tool_results = self._handle_tool_calls(tool_call, message)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_results
                    })

                # Делаем повторный запрос к GPT с результатами вызовов функций
                return self._generate_answer(messages, max_tokens)

            return completion.choices[0].message.content
        except Exception as e:
            return (f"Ну хз, не хотелось бы это обсуждать, кст у меня вылезает ошибка: {str(e)}\n"
                    f"Кстати а как переводится {completion.error['message']}")
