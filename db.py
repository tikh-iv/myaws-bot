from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import OperationalError
from datetime import datetime

Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    real_name = Column(String, default="User")  # Add this line


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.chat_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    chat = relationship('Chat', back_populates='messages')
    user = relationship('User')

class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    response_probability = Column(Integer, default=0.2)
    message_response_probability = Column(Integer, default=0.5)
    sticker_probability = Column(Integer, default=0.5)
    context_depth = Column(Integer, default=20)
    system_context = Column(Text, default="")
    max_tokens = Column(Integer, default=100)

    def __repr__(self):
        return (f"<Settings(response_probability={self.response_probability}, "
                f"message_response_probability={self.message_response_probability}, "
                f"sticker_probability={self.sticker_probability}, "
                f"context_depth={self.context_depth}, system_context='{self.system_context}', "
                f"max_tokens={self.max_tokens})>")

Chat.messages = relationship('Message', order_by=Message.timestamp, back_populates='chat')


class TelegramDBService:
    def __init__(self,
                 db_name: str):
        self.engine = create_engine(db_name, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.initialize_settings()

    def initialize_settings(self):
        session = self.Session()
        try:
            # Проверяем, есть ли уже настройки
            settings = session.query(Settings).first()
            if settings is None:
                # Если настроек нет, добавляем значения по умолчанию
                default_settings = Settings()
                session.add(default_settings)
                session.commit()
        finally:
            session.close()

    def get_settings(self):
        session = self.Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                return {
                    'response_probability': settings.response_probability,
                    'message_response_probability': settings.message_response_probability,
                    'sticker_probability': settings.sticker_probability,
                    'context_depth': settings.context_depth,
                    'system_context': settings.system_context,
                    'max_tokens': settings.max_tokens
                }
            else:
                return None
        finally:
            session.close()

    def update_settings(self, **kwargs):
        session = self.Session()
        try:
            settings = session.query(Settings).first()
            if settings:
                # Обновляем только те параметры, которые переданы в kwargs
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                session.commit()
        finally:
            session.close()

    def add_message(self,
                    chat_id: int,
                    user_id: int,
                    username: str,
                    message: str,
                    real_name: str = 'User',):
        '''
        Добавление Сообщения в БД и обработка параметров
        :param chat_id:
        :param user_id:
        :param username:
        :param message:
        :return:
        '''
        session = self.Session()
        try:
            # Получаем или создаем чат
            chat = session.query(Chat).filter_by(chat_id=chat_id).first()
            if chat is None:
                chat = Chat(chat_id=chat_id)
                session.add(chat)

            # Получаем или создаем пользователя
            user = session.query(User).filter_by(user_id=user_id).first()
            if user is None:
                user = User(user_id=user_id, username=username, real_name=real_name)
                session.add(user)

            # Создаем и добавляем сообщение
            msg = Message(chat_id=chat_id, user_id=user_id, message=message)
            session.add(msg)
            session.commit()
        finally:
            session.close()

    def get_messages(self,
                     chat_id: int,
                     limit: int = 10):
        session = self.Session()
        try:
            messages = session.query(Message).filter_by(chat_id=chat_id) \
                .order_by(Message.timestamp.desc()) \
                .limit(limit) \
                .all()
            messages.reverse()
            return [{'username': msg.user.username,
                     'real_name': msg.user.real_name,
                     'message': msg.message,
                     'timestamp': msg.timestamp,
                     'chat_id': msg.chat_id,
                     'user_id': msg.user_id} for msg in messages]
        finally:
            session.close()