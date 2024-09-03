from openai import OpenAI


class GPTModel:
    def __init__(self,
                 base_url: str,
                 gpt_api_key: str,
                 system_context: str,
                 model: str):
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


    def conversation_generate_answer(self,
                                     conversation: list,
                                     max_tokens: int = 100) -> str:
        messages = [{"role": "system", "content": self.system_context},]
        messages.extend(conversation)

        return self._generate_answer(messages, max_tokens)


    def _generate_answer(self,
                         messages: list,
                         max_tokens: int = 100):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens
            )
        except Exception as e:
            return f"Блин, хз, а как решить проблему {e}"
        try:
            return completion.choices[0].message.content
        except Exception as e:
            return (f"Ну хз, не хотелось бы это обсуждать, кст у меня вылезает ошибка: {str(e)}\n"
                    f"Кстати а как переводится {completion.error['message']}")
