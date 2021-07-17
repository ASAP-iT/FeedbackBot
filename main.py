from telegram import *
from telegram.ext import *

import code_generator
import models
from FeedbackMethods import FeedbackMethods
import config
from texts import *
from database import engine, SessionLocal
import transliterate
import sys
from datetime import datetime, timedelta

SELECT_TYPE, FEEDBACK, WANTS_REPLY = range(3)
CHOOSE_NAME, CREATE_WELCOME = range(2)
REPLY_TO_FEEDBACK = 0


def send_notifications(context: CallbackContext):
    chat_id = context.job.context
    context.bot.send_message(chat_id, "pizda")


def start(update: Update, context: CallbackContext) -> int:
    msg = update.message
    FeedbackMethods.create_user(SessionLocal(), update.message.from_user.id)

    jobs = context.job_queue.get_jobs_by_name("notification")[1:]
    print(jobs)
    for job in jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        send_notifications,
        interval=timedelta(seconds=5),
        context=msg.chat_id,
        first=datetime.now() + timedelta(seconds=2),
        name="notification",
    )
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


def create_feedback(update: Update, context: CallbackContext) -> int:
    msg = update.callback_query.message
    if not FeedbackMethods.is_admin(SessionLocal(), msg.chat_id):
        return ConversationHandler.END

    msg.edit_reply_markup(InlineKeyboardMarkup([]))
    msg.reply_text("пиши название")

    return CHOOSE_NAME


def create_feedback_back(update: Update, context: CallbackContext) -> int:
    create_feedback(update, context)
    return CHOOSE_NAME


def choose_name(update: Update, context: CallbackContext) -> int:
    txt = update.message.text

    try:
        transliterated = transliterate.translit(txt, reversed=True)
    except Exception:
        update.message.reply_text("писать что ли не умеешь")
        return CHOOSE_NAME

    transliterated = transliterated.replace(" ", "_")
    transliterated = transliterated.replace("\n", "_")
    context.user_data["feedback_name"] = transliterated

    if FeedbackMethods.name_exists(SessionLocal(), transliterated) is True:
        update.message.reply_text("Такое есть уже лох")
        return CHOOSE_NAME

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Назад", callback_data="create_back")],
        ]
    )

    update.message.reply_text(f"пиши приветствие {transliterated}", reply_markup=markup)

    return CREATE_WELCOME


def create_welcome(update: Update, context: CallbackContext) -> int:
    name = context.user_data["feedback_name"]
    welcome_txt = update.message.text

    if name is None or welcome_txt is None:
        update.message.reply_text("хуита брат")
        return ConversationHandler.END

    welcome, url = FeedbackMethods.create_welcome(
        SessionLocal(),
        update.message.chat_id,
        name,
        welcome_txt,
        update.message.bot.username,
    )
    if welcome is None:
        update.message.reply_text("хуита брат")
        return ConversationHandler.END

    update.message.reply_photo(
        caption=f"Название опроса: {name}\n\n"
        + "ссылочку откройте молодой человек"
        + f"\n{f'https://t.me/{update.message.bot.username}?start={name}'}",
        photo=open(url, "rb"),
    )

    return ConversationHandler.END


def my_feedbacks(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    data = update.callback_query.data

    context.user_data["feedback_scroll_ids"] = [
        x.id for x in FeedbackMethods.get_welcomes(SessionLocal(), msg.chat_id)
    ]

    if len(context.user_data["feedback_scroll_ids"]) == 0:
        msg.reply_text("Пока опросом немае")
        return ConversationHandler.END

    if context.user_data.get("current_feedback_scroll_id") is None:
        context.user_data["current_feedback_scroll_id"] = 0
    else:
        if data == "feedback_scroll_left":
            context.user_data["current_feedback_scroll_id"] -= 1
            if context.user_data["current_feedback_scroll_id"] < 0:
                context.user_data["current_feedback_scroll_id"] = (
                    len(context.user_data["feedback_scroll_ids"]) - 1
                )
        if data == "feedback_scroll_right":
            context.user_data["current_feedback_scroll_id"] += 1
            if (
                len(context.user_data["feedback_scroll_ids"])
                <= context.user_data["current_feedback_scroll_id"]
            ):
                context.user_data["current_feedback_scroll_id"] = 0

    current_id = context.user_data["current_feedback_scroll_id"]
    msg = update.callback_query.message

    welcome_id = context.user_data["feedback_scroll_ids"][current_id]

    welcome = FeedbackMethods.get_welcome_by_id(SessionLocal(), welcome_id)

    kb = [
        [
            InlineKeyboardButton("⬅️", callback_data="feedback_scroll_left"),
            InlineKeyboardButton("Edit", callback_data=f"welcome_edit-{welcome_id}"),
            InlineKeyboardButton("➡️️", callback_data="feedback_scroll_right"),
        ],
        [
            InlineKeyboardButton(
                "УДОЛИТЬ", callback_data=f"edit_welcome_delete-{welcome_id}"
            )
        ],
    ]

    markup = InlineKeyboardMarkup(kb)

    bot_name = update.callback_query.message.bot.username
    code_url = f"codes/{welcome.name}.png"
    code_generator.generate_qr_code(
        f"https://t.me/{bot_name}?start={welcome.name.lower()}", code_url
    )
    caption = (
        welcome.name
        + "\n"
        + welcome.message
        + f"\n\n{welcome_id}"
        + f"\n\n{f'https://t.me/{msg.bot.username}?start={welcome.name}'}"
    )

    try:
        msg.edit_media(
            media=InputMediaPhoto(media=open(code_url, "rb"), caption=caption),
            reply_markup=markup,
        )
    except:
        msg.delete()
        msg.reply_photo(
            open(welcome.code_url, "rb"), caption=caption, reply_markup=markup
        )

    return ConversationHandler.END


def select_type(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    type = update.callback_query.data

    if type == "complain":
        msg.edit_text("STR_REPLY_COMPLAIN")
    elif type == "praise":
        msg.edit_text("STR_REPLY_COMPLAIN")
    elif type == "suggest":
        msg.edit_text("STR_REPLY_COMPLAIN")
    elif type == "else":
        msg.edit_text("STR_REPLY_COMPLAIN")
    else:
        msg.edit_text("STR_REPLY_COMPLAIN")
        return ConversationHandler.END

    return FEEDBACK


def feedback_msg(update: Update, context: CallbackContext):
    context.user_data["user_msg"] = update.message.text
    context.user_data["feedback_msg_id"] = update.message.message_id

    if len(update.message.photo) > 0:
        context.user_data["user_image"] = update.message.photo
        context.user_data["user_msg"] = update.message.caption

    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data="yes"),
            InlineKeyboardButton("Нет", callback_data="no"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="prev_menu")],
    ]

    markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("чо-то типа", reply_markup=markup)

    return WANTS_REPLY


def wants_reply(update: Update, context: CallbackContext):
    data = update.callback_query.data
    msg = update.callback_query.message

    if data == "prev_menu":
        return select_type(update, context)

    if data == "yes":
        msg.edit_text("STR_FORWARD_MESSAGE")
    else:
        msg.edit_text("STR_THANKS_FOR_FEEDBACK")

    context.user_data["reply_type"] = data

    fb_msg = FeedbackMethods.create_feedback(
        SessionLocal(),
        welcome_id=context.user_data["welcome_id"],
        from_user_id=context.user_data["user_id"],
        message=context.user_data["user_msg"],
        msg_type=context.user_data["reply_type"],
        msg_id=context.user_data["feedback_msg_id"],
    )

    admin_id = fb_msg.welcome_message.chat_id

    kb = [
        [
            InlineKeyboardButton(
                "Хуй пизда отзыв ответить",
                callback_data=f"reply_to_feedback-{fb_msg.id}",
            )
        ]
    ]

    markup = InlineKeyboardMarkup(kb)

    msg.bot.send_message(admin_id, "пиздец отзыв оставили", reply_markup=markup)

    return ConversationHandler.END


def reply_feedback(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("Ответьте на хуй:")
    context.user_data["current_reply_msg_id"] = update.callback_query.message.message_id
    context.user_data["current_reply_feedback_id"] = int(
        update.callback_query.data.split("-")[1]
    )

    return REPLY_TO_FEEDBACK


def reply_message(update: Update, context: CallbackContext):
    msg = update.message.text

    update.message.bot.delete_message(
        chat_id=update.message.chat_id,
        message_id=context.user_data["current_reply_msg_id"],
    )

    feedback = FeedbackMethods.get_feedback(
        SessionLocal(), context.user_data["current_reply_feedback_id"]
    )

    update.message.bot.send_message(feedback.from_user_id, f"вам посылка\n{msg}")

    return ConversationHandler.END


def my_history(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    data = update.callback_query.data

    context.user_data["history_scroll_ids"] = [
        x.id for x in FeedbackMethods.get_feedbacks(SessionLocal(), msg.chat_id)
    ]

    if len(context.user_data["history_scroll_ids"]) == 0:
        msg.reply_text("Пока опросом немае")
        return ConversationHandler.END

    if context.user_data.get("current_history_scroll_id") is None:
        context.user_data["current_history_scroll_id"] = 0
    else:
        if data == "history_scroll_left":
            context.user_data["current_history_scroll_id"] -= 1
            if context.user_data["current_history_scroll_id"] < 0:
                context.user_data["current_history_scroll_id"] = (
                    len(context.user_data["history_scroll_ids"]) - 1
                )
        if data == "history_scroll_right":
            context.user_data["current_history_scroll_id"] += 1
            if (
                len(context.user_data["history_scroll_ids"])
                <= context.user_data["current_history_scroll_id"]
            ):
                context.user_data["current_history_scroll_id"] = 0

    current_id = context.user_data["current_history_scroll_id"]

    feedback_id = context.user_data["history_scroll_ids"][current_id]

    feedback = FeedbackMethods.get_feedback(SessionLocal(), feedback_id)

    kb = [
        [
            InlineKeyboardButton("⬅️", callback_data="history_scroll_left"),
            InlineKeyboardButton("➡️️", callback_data="history_scroll_right"),
        ]
    ]

    markup = InlineKeyboardMarkup(kb)

    text = f"{feedback.message} - {current_id}"

    try:
        msg.edit_text(text, reply_markup=markup)
    except:
        msg.delete()
        msg.reply_text(text, reply_markup=markup)

    return ConversationHandler.END


def welcome_edit(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    msg.delete()

    welcome_id = int(update.callback_query.data.split("-")[1])

    kb = [
        [
            InlineKeyboardButton(
                "edit title (you will need to edit qr codes)",
                callback_data=f"edit_welcome_title-{welcome_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "edit description",
                callback_data=f"edit_welcome_description-{welcome_id}",
            )
        ],
        [InlineKeyboardButton("<- back", callback_data=f"edit_welcome_back")],
    ]

    markup = InlineKeyboardMarkup(kb)

    msg.reply_text("чо редачить", reply_markup=markup)

    context.user_data["current_edit_id"] = welcome_id

    return ConversationHandler.END


def edit_welcome_back(update: Update, context: CallbackContext):
    my_feedbacks(update, context)

    return ConversationHandler.END


def welcome_edit_desc(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("back", callback_data="edit_welcome_back")]]
    )

    msg.edit_text("новый дескрипшн:", reply_markup=markup)

    return 0


def welcome_edit_title(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("back", callback_data="edit_welcome_back")]]
    )

    msg.edit_text("новый тайтл:", reply_markup=markup)

    return 0


def new_title(update: Update, context: CallbackContext):
    new_t = update.message.text

    try:
        transliterated = transliterate.translit(new_t, reversed=True)
    except Exception:
        update.message.reply_text("писать что ли не умеешь")
        return 0

    transliterated = transliterated.replace(" ", "_")
    transliterated = transliterated.replace("\n", "_")

    FeedbackMethods.edit_welcome_title(
        SessionLocal(), context.user_data["current_edit_id"], transliterated
    )
    update.message.reply_text("тайтл изменен!")

    return ConversationHandler.END


def new_description(update: Update, context: CallbackContext):
    new_d = update.message.text

    FeedbackMethods.edit_welcome_description(
        SessionLocal(), context.user_data["current_edit_id"], new_d
    )
    update.message.reply_text("дескрипшн изменен!")

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


def delete_welcome_ask(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    welcome_id = int(update.callback_query.data.split("-")[1])
    context.user_data["current_edit_id"] = welcome_id

    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("No", callback_data="no"),
                InlineKeyboardButton("Yes", callback_data="yes"),
            ],
            # [InlineKeyboardButton("back", callback_data="edit_welcome_back")]
        ]
    )
    msg.delete()
    msg.reply_text("Уверен?", reply_markup=markup)

    return 0


def delete_welcome(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    FeedbackMethods.delete_welcome(SessionLocal(), context.user_data["current_edit_id"])

    msg.edit_text("УДОЛЕНО")
    return ConversationHandler.END


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
