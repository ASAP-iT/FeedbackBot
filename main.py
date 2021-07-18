from telegram import *
from telegram.ext import *

import code_generator
import models
from FeedbackMethods import FeedbackMethods
import config
from bot_methods.feedback_methods import SELECT_TYPE, select_type, FEEDBACK, feedback_msg, WANTS_REPLY, wants_reply, \
    my_history
from bot_methods.welcome_methods import reply_feedback, REPLY_TO_FEEDBACK, reply_message, welcome_edit, \
    edit_welcome_back, welcome_edit_title, new_title, welcome_edit_desc, new_description, delete_welcome_ask, \
    delete_welcome, create_feedback, CHOOSE_NAME, CREATE_WELCOME, choose_name, create_welcome, create_feedback_back, \
    my_feedbacks
from texts import *
from database import engine, SessionLocal
import transliterate
import sys


def start(update: Update, context: CallbackContext) -> int:
    msg = update.message
    FeedbackMethods.create_user(SessionLocal(), update.message.from_user.id)
    context.user_data["user_id"] = msg.from_user.id

    if context.args is not None:
        if len(context.args) > 0:
            context.user_data["welcome_name"] = context.args[0]
            welcome_name = context.user_data["welcome_name"]

            welcome = FeedbackMethods.get_welcome(SessionLocal(), welcome_name)

            if welcome is None:
                if FeedbackMethods.delete_token(SessionLocal(), welcome_name) is None:
                    msg.reply_markdown_v2("naebat hotel?")
                    return ConversationHandler.END
                else:
                    FeedbackMethods.create_admin(SessionLocal(), msg.chat_id)
                    msg.reply_markdown_v2("pizda vi admin")
                    return ConversationHandler.END

            keyboard = [
                [InlineKeyboardButton("хуй", callback_data="complain")],
                [InlineKeyboardButton("pizda", callback_data="suggest")],
                [InlineKeyboardButton("asdf", callback_data="praise")],
                [InlineKeyboardButton("fdsa", callback_data="else")],
            ]

            markup = InlineKeyboardMarkup(keyboard)

            context.user_data["welcome_id"] = welcome.id
            context.user_data["welcome_name"] = welcome.name

            update.message.reply_text(
                f"{welcome.name}\n\n{welcome.message}", reply_markup=markup
            )

            return SELECT_TYPE

    kb = [
        [
            InlineKeyboardButton("🙋 Помощь", callback_data="start_help"),
            InlineKeyboardButton("💬 Мои ответы", callback_data="start_history"),
        ],
    ]

    if FeedbackMethods.is_admin(SessionLocal(), update.message.chat_id):
        kb.append(
            [
                InlineKeyboardButton("✉️ Создать опрос", callback_data="start_create"),
                InlineKeyboardButton("📩 Мои опросы", callback_data="start_feedbacks"),
            ]
        )
        kb.append(
            [
                InlineKeyboardButton(
                    "!Дать админку другому челу!", callback_data="start_grand_admin"
                )
            ]
        )
    markup = InlineKeyboardMarkup(kb)

    msg.reply_text("Привет иди нахуй это дев!", reply_markup=markup)

    return ConversationHandler.END


def help(update: Update, context: CallbackContext) -> int:
    print("help")
    if update.message is None:
        msg = update.callback_query.message
        print("callback")
    else:
        msg = update.message
        print("command")

    is_admin = FeedbackMethods.is_admin(SessionLocal(), msg.chat.id)
    if is_admin:
        new_text = STR_ADMIN_HELP
    else:
        new_text = STR_USER_HELP
    try:
        msg.edit_text(
            new_text, reply_markup=InlineKeyboardMarkup([]), parse_mode="HTML"
        )
    except:
        msg.reply_text(new_text, parse_mode="HTML")
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отмена")
    return ConversationHandler.END


def send_to_admins(bot, txt: str, parse_mode=None, **kwargs):
    for admin_id in config.admins:
        try:
            bot.sendMessage(text=txt, chat_id=admin_id, parse_mode=parse_mode)
        except Exception as err:
            print(err)


def grant_admin(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    is_admin = FeedbackMethods.is_admin(SessionLocal(), msg.chat_id)
    if is_admin:
        token = FeedbackMethods.create_token(SessionLocal())
        msg.reply_text(f"ваш токн: https://t.me/{msg.bot.username}?start={token}")


# pls, do not delete stuff below
# noinspection PyTypeChecker
def main():
    models.Base.metadata.create_all(bind=engine)

    import os

    os.system("mkdir codes")

    args = sys.argv

    if len(args) == 2:
        token = args[1]
    else:
        token = config.TOKEN

    print(token, args)
    print("STARTING FUCKING BOT")

    updater = Updater(token, use_context=True)

    send_to_admins(
        updater.bot, "Прогреваю код\n\n\nВылетаю разносить ебла пользователей"
    )

    dp = updater.dispatcher

    dp.add_handler(CallbackQueryHandler(grant_admin, pattern=r"start_grand_admin"))

    feedback = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_TYPE: [
                CallbackQueryHandler(
                    select_type, pattern=r"^(?:complain|suggest|praise|else)$"
                )
            ],
            FEEDBACK: [
                MessageHandler(
                    (Filters.text | (Filters.caption & Filters.photo))
                    & ~Filters.command,
                    feedback_msg,
                )
            ],
            WANTS_REPLY: [
                CallbackQueryHandler(wants_reply, pattern=r"^(?:yes|no|prev_menu)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        per_chat=True,
    )

    dp.add_handler(CallbackQueryHandler(help, pattern=r"start_help"))
    dp.add_handler(CommandHandler("help", help))

    reply = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(reply_feedback, pattern=r"reply_to_feedback-*")
        ],
        states={
            REPLY_TO_FEEDBACK: [
                MessageHandler(Filters.text & ~Filters.command, reply_message)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        per_chat=True,
    )
    dp.add_handler(reply)

    dp.add_handler(
        CallbackQueryHandler(
            my_feedbacks,
            pattern=r"^(?:start_feedbacks|feedback_scroll_left|feedback_scroll_right)$",
        )
    )

    dp.add_handler(
        CallbackQueryHandler(
            my_history,
            pattern=r"^(?:start_history|history_scroll_left|history_scroll_right)$",
        )
    )

    dp.add_handler(CallbackQueryHandler(welcome_edit, pattern=r"welcome_edit-*"))

    dp.add_handler(
        CallbackQueryHandler(edit_welcome_back, pattern=r"edit_welcome_back")
    )

    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    welcome_edit_title, pattern=r"edit_welcome_title-*"
                )
            ],
            states={
                0: [
                    MessageHandler(Filters.text & ~Filters.command, new_title),
                    CallbackQueryHandler(
                        edit_welcome_back, pattern=r"edit_welcome_back"
                    ),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CommandHandler("start", start),
            ],
            per_chat=True,
        )
    )

    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    welcome_edit_desc, pattern=r"edit_welcome_description-*"
                )
            ],
            states={
                0: [
                    MessageHandler(Filters.text & ~Filters.command, new_description),
                    CallbackQueryHandler(
                        edit_welcome_back, pattern=r"edit_welcome_back"
                    ),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CommandHandler("start", start),
            ],
            per_chat=True,
        )
    )

    # no
    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    delete_welcome_ask, pattern=r"edit_welcome_delete-*"
                )
            ],
            states={
                0: [
                    CallbackQueryHandler(delete_welcome, pattern=r"yes"),
                    CallbackQueryHandler(
                        edit_welcome_back, pattern=r"^(?:no|edit_welcome_back)$"
                    ),
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CommandHandler("start", start),
            ],
            per_chat=True,
        )
    )

    create = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_feedback, pattern=r"start_create")],
        states={
            CHOOSE_NAME: [MessageHandler(Filters.text & ~Filters.command, choose_name)],
            CREATE_WELCOME: [
                MessageHandler(Filters.text & ~Filters.command, create_welcome),
                CallbackQueryHandler(create_feedback_back, pattern=r"create_back"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        per_chat=True,
    )

    dp.add_handler(create)
    dp.add_handler(feedback)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
