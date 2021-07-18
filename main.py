from telegram import *
from telegram.ext import *

import models
from FeedbackMethods import FeedbackMethods
import config
from bot_methods.feedback_methods import (
    SELECT_TYPE,
    select_type,
    FEEDBACK,
    feedback_msg,
    WANTS_REPLY,
    wants_reply,
    my_history,
)
from bot_methods.welcome_methods import (
    reply_feedback,
    REPLY_TO_FEEDBACK,
    reply_message,
    welcome_edit,
    edit_welcome_back,
    welcome_edit_title,
    new_title,
    welcome_edit_desc,
    new_description,
    delete_welcome_ask,
    delete_welcome,
    create_feedback,
    CHOOSE_NAME,
    CREATE_WELCOME,
    choose_name,
    create_welcome,
    create_feedback_back,
    my_feedbacks,
    welcome_feedbacks,
)
from deeplink_generator import create_deeplink
from texts import *
from database import engine, SessionLocal
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
                    msg.reply_markdown_v2(STR_INVALID_LINK)
                    return ConversationHandler.END
                else:
                    FeedbackMethods.create_admin(SessionLocal(), msg.chat_id)
                    msg.reply_markdown_v2(STR_ADMIN_WELCOME)
                    return ConversationHandler.END

            keyboard = [
                [InlineKeyboardButton(STR_FEEDBACK_COMPLAIN, callback_data="complain")],
                [InlineKeyboardButton(STR_FEEDBACK_SUGGEST, callback_data="suggest")],
                [InlineKeyboardButton(STR_FEEDBACK_PRAISE, callback_data="praise")],
                [InlineKeyboardButton(STR_FEEDBACK_ELSE, callback_data="else")],
            ]

            markup = InlineKeyboardMarkup(keyboard)

            context.user_data["welcome_id"] = welcome.id
            context.user_data["welcome_name"] = welcome.name

            update.message.reply_text(
                STR_WELCOME_TEXT.format(name=welcome.name, message=welcome.message),
                reply_markup=markup,
            )

            return SELECT_TYPE

    kb = [
        [
            InlineKeyboardButton(STR_START_HELP, callback_data="start_help"),
            InlineKeyboardButton(STR_START_HISTORY, callback_data="start_history"),
        ],
    ]

    if FeedbackMethods.is_admin(SessionLocal(), update.message.chat_id):
        kb.append(
            [
                InlineKeyboardButton(
                    STR_START_CREATE_WELCOME, callback_data="start_create"
                ),
                InlineKeyboardButton(
                    STR_START_ME_WELCOMES, callback_data="start_feedbacks"
                ),
            ]
        )
        kb.append(
            [InlineKeyboardButton(STR_SHARE_ADMIN, callback_data="start_grand_admin")]
        )
    markup = InlineKeyboardMarkup(kb)

    msg.reply_text(STR_START_MSG, reply_markup=markup)

    return ConversationHandler.END


def help(update: Update, context: CallbackContext) -> int:
    if update.message is None:
        msg = update.callback_query.message
    else:
        msg = update.message

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
    update.message.reply_text(STR_CANCEL)
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
        msg.reply_text(
            STR_YOUR_TOKEN.format(token=create_deeplink(context.bot.username, token))
        )


def error_shit(update: Update, context: CallbackContext):
    return help(update, context)


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

    dp.add_handler(
        CallbackQueryHandler(grant_admin, pattern=fr"{CALLBACK_GRANT_ADMIN}")
    )

    feedback = ConversationHandler(
        entry_points=[CommandHandler(CMD_START, start)],
        states={
            SELECT_TYPE: [
                CallbackQueryHandler(select_type, pattern=fr"{CALLBACK_SELECT_TYPE}")
            ],
            FEEDBACK: [
                MessageHandler(
                    (Filters.text | (Filters.caption & Filters.photo))
                    & ~Filters.command,
                    feedback_msg,
                )
            ],
            WANTS_REPLY: [
                CallbackQueryHandler(wants_reply, pattern=fr"{CALLBACK_WANTS_REPLY}")
            ],
        },
        fallbacks=[
            CommandHandler(CMD_CANCEL, cancel),
            CommandHandler(CMD_START, start),
        ],
        per_chat=True,
    )

    dp.add_handler(CallbackQueryHandler(help, pattern=fr"{CALLBACK_HELP}"))
    dp.add_handler(CommandHandler(CMD_HELP, help))

    reply = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(reply_feedback, pattern=fr"{CALLBACK_REPLY_FEEDBACK}")
        ],
        states={
            REPLY_TO_FEEDBACK: [
                MessageHandler(Filters.text & ~Filters.command, reply_message)
            ]
        },
        fallbacks=[
            CommandHandler(CMD_CANCEL, cancel),
            CommandHandler(CMD_START, start),
        ],
        per_chat=True,
    )
    dp.add_handler(reply)

    dp.add_handler(
        CallbackQueryHandler(
            my_feedbacks,
            pattern=fr"{CALLBACK_MY_FEEDBACKS}",
        )
    )

    dp.add_handler(
        CallbackQueryHandler(
            my_history,
            pattern=fr"{CALLBACK_MY_HISTORY}",
        )
    )

    dp.add_handler(
        CallbackQueryHandler(welcome_edit, pattern=fr"{CALLBACK_WELCOME_EDIT}")
    )

    dp.add_handler(
        CallbackQueryHandler(edit_welcome_back, pattern=fr"{CALLBACK_WELCOME_BACK}")
    )

    dp.add_handler(
        CallbackQueryHandler(
            welcome_feedbacks, pattern=fr"{CALLBACK_HISTORY_FEEDBACKS}"
        )
    )

    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    welcome_edit_title, pattern=fr"{CALLBACK_EDIT_WELCOME_TITLE}"
                )
            ],
            states={
                0: [
                    MessageHandler(Filters.text & ~Filters.command, new_title),
                    CallbackQueryHandler(
                        edit_welcome_back, pattern=fr"{CALLBACK_WELCOME_BACK}"
                    ),
                ]
            },
            fallbacks=[
                CommandHandler(CMD_CANCEL, cancel),
                CommandHandler(CMD_START, start),
            ],
            per_chat=True,
        )
    )

    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    welcome_edit_desc, pattern=fr"{CALLBACK_EDIT_WELCOME_DESCRIPTION}"
                )
            ],
            states={
                0: [
                    MessageHandler(Filters.text & ~Filters.command, new_description),
                    CallbackQueryHandler(
                        edit_welcome_back, pattern=fr"{CALLBACK_WELCOME_BACK}"
                    ),
                ]
            },
            fallbacks=[
                CommandHandler(CMD_CANCEL, cancel),
                CommandHandler(CMD_START, start),
            ],
            per_chat=True,
        )
    )

    # no
    dp.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(delete_welcome_ask, pattern=fr"{CALLBACK_DELETE}")
            ],
            states={
                0: [
                    CallbackQueryHandler(delete_welcome, pattern=fr"{CALLBACK_YES}"),
                    CallbackQueryHandler(
                        edit_welcome_back, pattern=fr"{CALLBACK_WELCOME_BACK_NO}"
                    ),
                ]
            },
            fallbacks=[
                CommandHandler(CMD_CANCEL, cancel),
                CommandHandler(CMD_START, start),
            ],
            per_chat=True,
        )
    )

    create = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(create_feedback, pattern=fr"{CALLBACK_CREATE}")
        ],
        states={
            CHOOSE_NAME: [MessageHandler(Filters.text & ~Filters.command, choose_name)],
            CREATE_WELCOME: [
                MessageHandler(Filters.text & ~Filters.command, create_welcome),
                CallbackQueryHandler(
                    create_feedback_back, pattern=fr"{CALLBACK_CREATE_BACK}"
                ),
            ],
        },
        fallbacks=[
            CommandHandler(CMD_CANCEL, cancel),
            CommandHandler(CMD_START, start),
        ],
        per_chat=True,
    )

    dp.add_handler(create)
    dp.add_handler(feedback)

    dp.add_handler(MessageHandler(Filters.text, error_shit))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
