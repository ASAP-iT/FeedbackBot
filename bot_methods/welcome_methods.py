# welcome_methods.py
# FeedbackBot
# Created by romanesin on 18.07.2021
import transliterate
from telegram import Update, InlineKeyboardMarkup, InputMediaPhoto, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

import code_generator
from FeedbackMethods import FeedbackMethods
from database import SessionLocal
from texts import *
from deeplink_generator import create_deeplink

CHOOSE_NAME, CREATE_WELCOME = range(2)
REPLY_TO_FEEDBACK = 0


def create_feedback_back(update: Update, context: CallbackContext) -> int:
    create_feedback(update, context)
    return CHOOSE_NAME


def create_feedback(update: Update, context: CallbackContext) -> int:
    msg = update.callback_query.message

    db = SessionLocal()
    if not FeedbackMethods.is_admin(db, msg.chat_id):
        return ConversationHandler.END

    msg.edit_reply_markup(InlineKeyboardMarkup([]))
    msg.reply_text(STR_NEW_WELCOME_NAME)

    db.close()
    return CHOOSE_NAME


def choose_name(update: Update, context: CallbackContext) -> int:
    txt = update.message.text
    db = SessionLocal()

    try:
        transliterated = transliterate.translit(txt, reversed=True)
    except Exception:
        update.message.reply_text(STR_INVALID_WELCOME_NAME)
        return CHOOSE_NAME

    transliterated = transliterated.replace(" ", "_")
    transliterated = transliterated.replace("\n", "_")
    context.user_data["feedback_name"] = transliterated

    if FeedbackMethods.name_exists(db, transliterated) is True:
        update.message.reply_text(STR_WELCOME_NAME_TAKEN)
        return CHOOSE_NAME

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(STR_BACK, callback_data=CALLBACK_CREATE_BACK)],
        ]
    )

    update.message.reply_text(STR_NEW_WELCOME_MESSAGE, reply_markup=markup)

    db.close()
    return CREATE_WELCOME


def create_welcome(update: Update, context: CallbackContext) -> int:
    name = context.user_data["feedback_name"]
    welcome_txt = update.message.text
    db = SessionLocal()

    if name is None or welcome_txt is None:
        update.message.reply_text(STR_ERROR)

        db.close()
        return ConversationHandler.END

    welcome, url = FeedbackMethods.create_welcome(
        db,
        update.message.chat_id,
        name,
        welcome_txt,
        update.message.bot.username,
    )
    if welcome is None:
        update.message.reply_text(STR_ERROR)

        db.close()
        return ConversationHandler.END

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(STR_TO_MENU, callback_data=CMD_START)]]
    )
    update.message.reply_photo(
        caption=STR_WELCOME_OVERVIEW.format(
            name=name,
            message=welcome_txt,
            link=create_deeplink(context.bot.username, name),
        ),
        photo=open(url, "rb"),
        reply_markup=markup,
    )

    db.close()
    return ConversationHandler.END


def my_feedbacks(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    data = update.callback_query.data
    db = SessionLocal()

    context.user_data["feedback_scroll_ids"] = [
        x.id for x in FeedbackMethods.get_welcomes(db, msg.chat_id)
    ]

    if len(context.user_data["feedback_scroll_ids"]) == 0:
        msg.reply_text(STR_NO_WELCOMES)
        db.close()
        return ConversationHandler.END

    if context.user_data.get("current_feedback_scroll_id") is None:
        context.user_data["current_feedback_scroll_id"] = 0
    else:
        if data == CALLBACK_FEEDBACK_LEFT:
            context.user_data["current_feedback_scroll_id"] -= 1
        if data == CALLBACK_FEEDBACK_RIGHT:
            context.user_data["current_feedback_scroll_id"] += 1

        if (
            len(context.user_data["feedback_scroll_ids"])
            <= context.user_data["current_feedback_scroll_id"]
        ):
            context.user_data["current_feedback_scroll_id"] = 0
        if context.user_data["current_feedback_scroll_id"] < 0:
            context.user_data["current_feedback_scroll_id"] = (
                len(context.user_data["feedback_scroll_ids"]) - 1
            )

    current_id = context.user_data["current_feedback_scroll_id"]
    msg = update.callback_query.message

    welcome_id = context.user_data["feedback_scroll_ids"][current_id]

    welcome = FeedbackMethods.get_welcome_by_id(db, welcome_id)

    context.user_data["welcome_id_scroll"] = welcome.id

    kb = [
        [
            InlineKeyboardButton(STR_ARROW_LEFT, callback_data=CALLBACK_FEEDBACK_LEFT),
            InlineKeyboardButton(
                STR_WELCOME_EDIT, callback_data=f"welcome_edit-{welcome_id}"
            ),
            InlineKeyboardButton(
                STR_ARROW_RIGHT, callback_data=CALLBACK_FEEDBACK_RIGHT
            ),
        ],
        [
            InlineKeyboardButton(
                STR_WELCOME_SHOW_FEEDBACKS, callback_data=f"his_feedbacks"
            ),
            InlineKeyboardButton(
                STR_WELCOME_DELETE, callback_data=f"edit_welcome_delete-{welcome_id}"
            ),
        ],
        [
            InlineKeyboardButton(STR_TO_MENU, callback_data=CMD_START),
        ],
    ]

    markup = InlineKeyboardMarkup(kb)

    code_url = f"codes/{welcome.name}.png"
    code_generator.generate_qr_code(
        create_deeplink(context.bot.username, welcome.name), code_url
    )
    caption = STR_WELCOME_OVERVIEW.format(
        name=welcome.name,
        message=welcome.message,
        link=create_deeplink(context.bot.username, welcome.name),
    )

    # if len(context.user_data["feedback_scroll_ids"]) == 1:
    #     return ConversationHandler.END

    if msg.caption == caption.strip():
        db.close()
        return ConversationHandler.END

    try:
        msg.edit_media(
            media=InputMediaPhoto(media=open(code_url, "rb"), caption=caption),
            reply_markup=markup,
        )
    except Exception as e:
        try:
            msg.delete()
        except:
            pass
        msg.reply_photo(
            open(welcome.code_url, "rb"), caption=caption, reply_markup=markup
        )

    db.close()
    return ConversationHandler.END


def welcome_edit(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    msg.delete()

    welcome_id = int(update.callback_query.data.split("-")[1])

    kb = [
        [
            InlineKeyboardButton(
                STR_WELCOME_EDIT_TITLE,
                callback_data=f"edit_welcome_title-{welcome_id}",
            )
        ],
        [
            InlineKeyboardButton(
                STR_WELCOME_EDIT_DESCRIPTION,
                callback_data=f"edit_welcome_description-{welcome_id}",
            )
        ],
        [InlineKeyboardButton(STR_ARROW_LEFT, callback_data=CALLBACK_WELCOME_BACK)],
    ]

    markup = InlineKeyboardMarkup(kb)

    msg.reply_text(STR_WELCOME_WHAT_TO_EDIT, reply_markup=markup)

    context.user_data["current_edit_id"] = welcome_id

    return ConversationHandler.END


def edit_welcome_back(update: Update, context: CallbackContext):
    my_feedbacks(update, context)

    return ConversationHandler.END


def welcome_edit_desc(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(STR_ARROW_LEFT, callback_data=CALLBACK_WELCOME_BACK)]]
    )

    msg.edit_text(STR_WELCOME_NEW_DESCRPTION, reply_markup=markup)

    return 0


def welcome_edit_title(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(STR_ARROW_LEFT, callback_data=CALLBACK_WELCOME_BACK)]]
    )

    msg.edit_text(STR_WELCOME_NEW_TITLE, reply_markup=markup)

    return 0


def new_title(update: Update, context: CallbackContext):
    new_t = update.message.text

    try:
        transliterated = transliterate.translit(new_t, reversed=True)
    except Exception:
        update.message.reply_text(STR_INVALID_WELCOME_NAME)
        return 0

    transliterated = transliterated.replace(" ", "_")
    transliterated = transliterated.replace("\n", "_")

    db = SessionLocal()
    FeedbackMethods.edit_welcome_title(
        db, context.user_data["current_edit_id"], transliterated
    )
    update.message.reply_text(STR_WELCOME_TITLE_EDITED)

    db.close()
    return ConversationHandler.END


def new_description(update: Update, context: CallbackContext):
    new_d = update.message.text
    db = SessionLocal()

    FeedbackMethods.edit_welcome_description(
        db, context.user_data["current_edit_id"], new_d
    )
    update.message.reply_text(STR_WELCOME_DESC_EDITED)

    db.close()
    return ConversationHandler.END


def delete_welcome(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    db = SessionLocal()

    FeedbackMethods.delete_welcome(db, context.user_data["current_edit_id"])

    msg.edit_text(STR_WELCOME_DELETED)

    db.close()

    from main import start

    start(update, context)

    return ConversationHandler.END


def delete_welcome_ask(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    welcome_id = int(update.callback_query.data.split("-")[1])
    context.user_data["current_edit_id"] = welcome_id

    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(STR_YES, callback_data=CALLBACK_YES),
                InlineKeyboardButton(STR_NO, callback_data=CALLBACK_NO),
            ],
            # [InlineKeyboardButton("back", callback_data="edit_welcome_back")]
        ]
    )
    msg.delete()
    msg.reply_text(STR_DELETE_ASK, reply_markup=markup)

    return 0


def reply_feedback(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("Напишите ответ:")
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

    db = SessionLocal()

    feedback = FeedbackMethods.get_feedback(
        db, context.user_data["current_reply_feedback_id"]
    )

    feedback.response = msg
    db.commit()

    update.message.bot.send_message(
        feedback.from_user_id,
        STR_FEEDBACK_REPLY.format(name=feedback.welcome_message.name, message=msg),
    )

    db.close()
    return ConversationHandler.END


def welcome_feedbacks(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    data = update.callback_query.data

    if data == "back":
        edit_welcome_back(update, context)
        return ConversationHandler.END

    db = SessionLocal()
    context.user_data["history_feedbacks_scroll_ids"] = [
        x.id
        for x in FeedbackMethods.get_welcome_feedbacks(
            db, msg.chat_id, context.user_data["welcome_id_scroll"]
        )
    ]

    if len(context.user_data["history_feedbacks_scroll_ids"]) == 0:
        msg.reply_text(STR_NO_FEEDBACKS)

        db.close()
        return ConversationHandler.END

    if context.user_data.get("current_history_feed_scroll_id") is None:
        context.user_data["current_history_feed_scroll_id"] = 0
    else:
        if data == CALLBACK_HISTORY_FEED_LEFT:
            context.user_data["current_history_feed_scroll_id"] -= 1
        if data == CALLBACK_HISTORY_FEED_RIGHT:
            context.user_data["current_history_feed_scroll_id"] += 1
        if (
            len(context.user_data["history_feedbacks_scroll_ids"])
            <= context.user_data["current_history_feed_scroll_id"]
        ):
            context.user_data["current_history_feed_scroll_id"] = 0
        if context.user_data["current_history_feed_scroll_id"] < 0:
            context.user_data["current_history_feed_scroll_id"] = (
                len(context.user_data["history_scroll_ids"]) - 1
            )

    current_id = context.user_data["current_history_feed_scroll_id"]

    feedback_id = context.user_data["history_feedbacks_scroll_ids"][current_id]

    feedback = FeedbackMethods.get_feedback(SessionLocal(), feedback_id)

    kb = [
        [
            InlineKeyboardButton(
                STR_ARROW_LEFT, callback_data=CALLBACK_HISTORY_FEED_LEFT
            ),
            InlineKeyboardButton(
                STR_ARROW_RIGHT, callback_data=CALLBACK_HISTORY_FEED_RIGHT
            ),
        ],
        [InlineKeyboardButton(STR_BACK, callback_data=CALLBACK_WELCOME_BACK)],
    ]

    markup = InlineKeyboardMarkup(kb)

    if feedback.response is not None:
        text = STR_HISTORY_FEEDBACK_ITEM.format(
            name=feedback.welcome_message.name,
            message=feedback.message,
            response=feedback.response,
        )
    else:
        text = STR_HISTORY_ITEM.format(
            name=feedback.welcome_message.name, message=feedback.message
        )

    if msg.text == text.strip():
        db.close()
        return ConversationHandler.END

    try:
        msg.edit_text(text, reply_markup=markup)
    except:
        try:
            msg.delete()
        except:
            pass
        msg.reply_text(text, reply_markup=markup)

    db.close()
    return ConversationHandler.END
