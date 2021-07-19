# database.py
# FeedbackBot
# Created by romanesin on 16.07.2021

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv("feedback-bot-dev.env")
url = os.environ.get("DB_URL")

if url is None:
    load_dotenv("feedback-bot.env")
    url = os.environ.get("DB_URL")

engine = create_engine(url, pool_size=20, max_overflow=0)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
