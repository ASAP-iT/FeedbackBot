# welcome_methods.py
# FeedbackBot
# Created by romanesin on 18.07.2021
import transliterate
from telegram import Update, InlineKeyboardMarkup, InputMediaPhoto, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

import code_generator
from FeedbackMethods import FeedbackMethods
from database import SessionLocal

CHOOSE_NAME, CREATE_WELCOME = range(2)
REPLY_TO_FEEDBACK = 0


def create_feedback_back(update: Update, context: CallbackContext) -> int:
    create_feedback(update, context)
    return CHOOSE_NAME


def create_feedback(update: Update, context: CallbackContext) -> int:
    msg = update.callback_query.message
    if not FeedbackMethods.is_admin(SessionLocal(), msg.chat_id):
        return ConversationHandler.END

    msg.edit_reply_markup(InlineKeyboardMarkup([]))
    msg.reply_text("пиши название")

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


def delete_welcome(update: Update, context: CallbackContext):
    msg = update.callback_query.message

    FeedbackMethods.delete_welcome(SessionLocal(), context.user_data["current_edit_id"])

    msg.edit_text("УДОЛЕНО")
    return ConversationHandler.END


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
