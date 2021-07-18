# deeplink_generator.py
# FeedbackBot
# Created by romanesin on 18.07.2021

def create_deeplink(botname: str, start: str):
    return f"https://t.me/{botname}?start={start}"