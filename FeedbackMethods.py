# FeedbackMethods.py
# FeedbackBot
# Created by romanesin on 16.07.2021
import datetime
import secrets
from typing import List

from sqlalchemy.orm import Session
from models import FeedbackMessage, WelcomeMessage, AdminUser, OneTimeToken, User
from code_generator import generate_qr_code


class FeedbackMethods:
    @staticmethod
    def create_feedback(
        db: Session,
        welcome_id: int,
        msg_type: str,
        message: str,
        from_user_id: int,
        msg_id: int,
    ) -> FeedbackMessage:
        feedback = FeedbackMessage(
            type=msg_type,
            message=message,
            from_user_id=from_user_id,
            welcome_message_id=welcome_id,
            feedback_msg_id=msg_id,
        )

        db.add(feedback)
        db.flush()
        db.commit()
        db.refresh(feedback)

        return feedback

    @staticmethod
    def get_welcome(db: Session, feedback_name: str) -> WelcomeMessage:
        return (
            db.query(WelcomeMessage)
            .filter(WelcomeMessage.name == feedback_name)
            .first()
        )

    @staticmethod
    def get_welcome_by_id(db: Session, welcome_id: int) -> WelcomeMessage:
        return db.query(WelcomeMessage).filter(WelcomeMessage.id == welcome_id).first()

    @staticmethod
    def name_exists(db: Session, name: str) -> bool:
        return (
            db.query(WelcomeMessage).filter(WelcomeMessage.name == name).first()
            is not None
        )

    @staticmethod
    def create_welcome(
        db: Session, user_id: int, name: str, message: str, bot_name: str
    ):
        if FeedbackMethods.name_exists(db, name) is True:
            return None, None

        code_url = f"codes/{name}.png"
        generate_qr_code(f"https://t.me/{bot_name}?start={name.lower()}", code_url)

        welcome = WelcomeMessage(
            chat_id=user_id, name=name, message=message, code_url=code_url
        )

        db.add(welcome)
        db.commit()
        return welcome, code_url

    @staticmethod
    def can_feedback(db: Session, user_id: int, welcome_id: int) -> bool:
        last_item: List[FeedbackMessage] = (
            db.query(FeedbackMessage)
            .filter(
                FeedbackMessage.welcome_message_id == welcome_id
                and FeedbackMessage.from_user_id == user_id
            )
            .all()
        )

        l = list(
            filter(
                lambda x: x.sent_date
                > datetime.datetime.now() - datetime.timedelta(days=1),
                last_item,
            )
        )
        return len(l) == 0

    @staticmethod
    def get_feedback(db: Session, feedback_id: int) -> FeedbackMessage:
        feedback = (
            db.query(FeedbackMessage).filter(FeedbackMessage.id == feedback_id).first()
        )
        if feedback is not None:
            return feedback

    @staticmethod
    def mark_feedback_has_response(
        db: Session, feedback_id: int, response: str
    ) -> None:
        fb = FeedbackMethods.get_feedback(db, feedback_id)
        if fb is not None:
            feedback: FeedbackMessage = (
                db.query(FeedbackMessage)
                .filter(FeedbackMessage.id == feedback_id)
                .first()
            )
            if feedback is None:
                return
            feedback.has_response = True
            feedback.response = response
            db.commit()

    @staticmethod
    def set_chats_with_prefix(
        db: Session, prefix: str, user_id: int, chat_id: int
    ) -> List[WelcomeMessage]:
        feedbacks = (
            db.query(WelcomeMessage).filter(WelcomeMessage.chat_id == user_id).all()
        )

        welcomes = []
        for welcome in feedbacks:
            if welcome.name.startswith(prefix):
                welcome.chat_id = chat_id
                welcomes.append(welcome)

        db.commit()

        return welcomes

    @staticmethod
    def get_all(db: Session, chat_id: int) -> List[WelcomeMessage]:
        return db.query(WelcomeMessage).filter(WelcomeMessage.chat_id == chat_id).all()

    @staticmethod
    def remove(db: Session, name: str, chat_id: int):
        welcome = (
            db.query(WelcomeMessage)
            .filter(WelcomeMessage.name == name)
            .filter(WelcomeMessage.chat_id == chat_id)
            .first()
        )

        if welcome is None:
            return None

        feedbacks = (
            db.query(WelcomeMessage)
            .filter(FeedbackMessage.welcome_message_id == welcome.id)
            .all()
        )
        for feedback in feedbacks:
            db.delete(feedback)
        db.delete(welcome)

        db.commit()

        return 1

    @staticmethod
    def edit_welcome_name(db: Session, welcome_id: int, chat_id: int, new_text: str):
        print(welcome_id, chat_id, new_text)
        welcome: WelcomeMessage = (
            db.query(WelcomeMessage)
            .filter(WelcomeMessage.id == welcome_id)
            .filter(WelcomeMessage.chat_id == chat_id)
            .first()
        )

        if welcome is None:
            return None

        welcome.name = new_text
        print(new_text)
        db.commit()

        return 1

    @staticmethod
    def edit_welcome_full_name(
        db: Session, welcome_id: str, chat_id: int, new_title: str
    ):
        print(welcome_id, chat_id, new_title)
        welcome: WelcomeMessage = (
            db.query(WelcomeMessage)
            .filter(WelcomeMessage.id == welcome_id)
            .filter(WelcomeMessage.chat_id == chat_id)
            .first()
        )

        if welcome is None:
            return None

        welcome.full_name = new_title
        print(new_title)
        db.commit()

        return 1

    @staticmethod
    def edit_welcome_msg(db: Session, welcome_id: int, chat_id: int, new_msg: str):
        print(welcome_id, chat_id, new_msg)
        welcome: WelcomeMessage = (
            db.query(WelcomeMessage)
            .filter(WelcomeMessage.id == welcome_id)
            .filter(WelcomeMessage.chat_id == chat_id)
            .first()
        )

        if welcome is None:
            return None

        welcome.message = new_msg
        print(new_msg)
        db.commit()

        return 1

    @staticmethod
    def set_feedback_loved(db: Session, feedback_id: int, loved: bool):
        feedback: FeedbackMessage = (
            db.query(FeedbackMessage).filter(FeedbackMessage.id == feedback_id).first()
        )
        if feedback is None:
            return
        feedback.loved_response = loved

        db.commit()
        return feedback

    @staticmethod
    def add_admin_chat_msg_id(db: Session, feedback_id: int, message_id: int):
        feedback: FeedbackMessage = (
            db.query(FeedbackMessage).filter(FeedbackMessage.id == feedback_id).first()
        )
        if feedback is None:
            return
        feedback.admin_chat_msg_id = message_id
        db.commit()
        return feedback

    @staticmethod
    def get_admin_chat_message_id(db: Session, feedback_id: int) -> int:
        feedback: FeedbackMessage = (
            db.query(FeedbackMessage).filter(FeedbackMessage.id == feedback_id).first()
        )
        if feedback is None:
            return
        return feedback.admin_chat_msg_id

    @staticmethod
    def is_admin(db: Session, user_id: int) -> bool:
        user = db.query(AdminUser).filter(AdminUser.user_id == user_id).first()
        return user is not None

    @staticmethod
    def delete_token(db: Session, token: str):
        token = db.query(OneTimeToken).filter(OneTimeToken.token == token).first()

        if token is None:
            return None

        db.delete(token)
        db.commit()
        return 1

    @staticmethod
    def create_token(db: Session) -> str:
        token = OneTimeToken(token=secrets.token_hex(16))

        db.add(token)
        db.commit()

        return token.token

    @staticmethod
    def create_admin(db: Session, user_id: int):
        admin = AdminUser(user_id=user_id)

        db.add(admin)
        try:
            db.commit()
        except:
            pass

    @staticmethod
    def create_user(db: Session, user_id: int):
        if db.query(User).filter(User.user_id == user_id).first() is not None:
            return

        user = User(user_id=user_id)
        db.add(user)
        db.commit()

    @staticmethod
    def get_welcomes(db: Session, chat_id: int) -> List[WelcomeMessage]:
        return db.query(WelcomeMessage).filter(WelcomeMessage.chat_id == chat_id).all()

    @staticmethod
    def get_feedbacks(db: Session, chat_id: int) -> List[FeedbackMessage]:
        return (
            db.query(FeedbackMessage)
            .filter(FeedbackMessage.from_user_id == chat_id)
            .all()
        )

    @staticmethod
    def edit_welcome_title(db: Session, welcome_id: int, title: str):
        welcome: WelcomeMessage = (
            db.query(WelcomeMessage).filter(WelcomeMessage.id == welcome_id).first()
        )
        if welcome is not None:
            welcome.name = title
            welcome.code_url = f"codes/{welcome.name}.png"
            db.commit()

    @staticmethod
    def edit_welcome_description(db: Session, welcome_id: int, description: str):
        welcome = (
            db.query(WelcomeMessage).filter(WelcomeMessage.id == welcome_id).first()
        )
        if welcome is not None:
            welcome.message = description
            db.commit()

    @staticmethod
    def delete_welcome(db: Session, welcome_id: int):
        welcome: WelcomeMessage = (
            db.query(WelcomeMessage).filter(WelcomeMessage.id == welcome_id).first()
        )

        feedbacks = (
            db.query(WelcomeMessage)
            .filter(FeedbackMessage.welcome_message_id == welcome.id)
            .all()
        )
        for feedback in feedbacks:
            db.delete(feedback)
        db.commit()
        db.flush()
        db.delete(welcome)
        db.commit()
