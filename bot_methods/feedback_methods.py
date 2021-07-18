# feedback_methods.py
# FeedbackBot
# Created by romanesin on 18.07.2021
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from FeedbackMethods import FeedbackMethods
from database import SessionLocal
from texts import *

SELECT_TYPE, FEEDBACK, WANTS_REPLY = range(3)


def select_type(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    type = update.callback_query.data

    if type == "complain":
        msg.edit_text(STR_FEEDBACK_COMPLAIN_D)
    elif type == "praise":
        msg.edit_text(STR_FEEDBACK_PRAISE_D)
    elif type == "suggest":
        msg.edit_text(STR_FEEDBACK_SUGGEST_D)
    elif type == "else":
        msg.edit_text(STR_FEEDBACK_ELSE_D)
    else:
        msg.edit_text(STR_ERROR)
        return ConversationHandler.END

    context.user_data["reply_type"] = type

    return FEEDBACK


def feedback_msg(update: Update, context: CallbackContext):
    context.user_data["user_msg"] = update.message.text
    context.user_data["feedback_msg_id"] = update.message.message_id

    if len(update.message.photo) > 0:
        context.user_data["user_image"] = update.message.photo
        context.user_data["user_msg"] = update.message.caption

    keyboard = [
        [
            InlineKeyboardButton(STR_YES, callback_data=CALLBACK_YES),
            InlineKeyboardButton(STR_NO, callback_data=CALLBACK_NO),
        ],
        [InlineKeyboardButton(STR_BACK, callback_data=CALLBACK_PREV_MENU)],
    ]

    markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(STR_WANTS_REPLY, reply_markup=markup)

    return WANTS_REPLY


def wants_reply(update: Update, context: CallbackContext):
    data = update.callback_query.data
    msg = update.callback_query.message

    if data == CALLBACK_PREV_MENU:
        return select_type(update, context)

    if data == CALLBACK_YES:
        msg.edit_text(STR_FORWARD)
    else:
        msg.edit_text(STR_THANKS_FOR_FEEDBACK)

    fb_msg = FeedbackMethods.create_feedback(
        SessionLocal(),
        welcome_id=context.user_data["welcome_id"],
        from_user_id=context.user_data["user_id"],
        message=context.user_data["user_msg"],
        msg_type=context.user_data["reply_type"],
        msg_id=context.user_data["feedback_msg_id"],
    )

    admin_id = fb_msg.welcome_message.chat_id

    if data == CALLBACK_YES:
        kb = [
            [
                InlineKeyboardButton(
                    STR_REPLY_TO_FEEDBACK,
                    callback_data=f"reply_to_feedback-{fb_msg.id}",
                )
            ]
        ]
    else:
        kb = []

    markup = InlineKeyboardMarkup(kb)

    msg.bot.send_message(
        admin_id,
        STR_NEW_FEEDBACK.format(
            name=fb_msg.welcome_message.name, message=fb_msg.message
        ),
        reply_markup=markup,
    )

    return ConversationHandler.END


def my_history(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    data = update.callback_query.data

    context.user_data["history_scroll_ids"] = [
        x.id for x in FeedbackMethods.get_feedbacks(SessionLocal(), msg.chat_id)
    ]

    if len(context.user_data["history_scroll_ids"]) == 0:
        msg.reply_text(STR_NO_FEEDBACKS)
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
            InlineKeyboardButton(STR_ARROW_LEFT, callback_data=CALLBACK_HISTORY_LEFT),
            InlineKeyboardButton(STR_ARROW_RIGHT, callback_data=CALLBACK_HISTORY_RIGHT),
        ]
    ]

    markup = InlineKeyboardMarkup(kb)

    text = STR_HISTORY_ITEM.format(
        name=feedback.welcome_message.name, message=feedback.message
    )

    try:
        msg.edit_text(text, reply_markup=markup)
    except:
        msg.delete()
        msg.reply_text(text, reply_markup=markup)

    return ConversationHandler.END
