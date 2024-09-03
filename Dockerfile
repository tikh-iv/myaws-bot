FROM python:3.9-slim
LABEL authors="ivan"

WORKDIR /

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TELEGRAM_API_TOKEN=default_api_key
ENV DB_NAME=sqlite:///telegram_bot.sqlite
ENV BASE_URL=https://openrouter.ai/api/v1
ENV GPT_API_KEY=default_api_key
ENV MODEL=openai/gpt-4o-mini
ENV SYSTEM_CONTEXT=./context.txt
ENV BOT_NAMES=MeowSavbot,pawnpaw

CMD ["python", "main.py"]