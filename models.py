# models.py
# FeedbackBot
# Created by romanesin on 16.07.2021

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    BigInteger
)

from sqlalchemy.orm import relationship
from database import Base


class WelcomeMessage(Base):
    __tablename__ = "welcome_messages"

    id = Column(Integer, primary_key=True)
    # title = Column(String)
    name = Column(String, unique=True)
    message = Column(String)
    code_url = Column(String, unique=True)
    chat_id = Column(BigInteger)


class FeedbackMessage(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    message = Column(String)
    from_user_id = Column(Integer)
    sent_date = Column(DateTime, default=datetime.now)
    has_response = Column(Boolean, default=False)
    response = Column(String)
    loved_response = Column(Boolean, default=None)
    admin_chat_msg_id = Column(Integer)
    feedback_msg_id = Column(Integer)

    welcome_message_id = Column(Integer, ForeignKey("welcome_messages.id"))
    welcome_message = relationship("WelcomeMessage")


class AdminUser(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)


class OneTimeToken(Base):
    __tablename__ = "one_time_token"

    id = Column(Integer, primary_key=True)
    token = Column(String)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)