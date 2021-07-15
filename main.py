from telegram import *
from telegram.ext import *

from FeedbackMethods import FeedbackMethods
import config
import models
from database import engine, SessionLocal
import transliterate

CHOOSE_NAME, CREATE_WELCOME = range(2)


def start(update: Update, context: CallbackContext) -> int:
    FeedbackMethods.create_user(SessionLocal(), update.message.from_user.id)

    kb = [
        [InlineKeyboardButton("🙋 Помощь", callback_data="start_help")],
        [InlineKeyboardButton("💬 Мои ответы", callback_data="start_history")],
    ]

    if FeedbackMethods.is_admin(SessionLocal(), update.message.chat_id):
        kb.append([InlineKeyboardButton("✉️ Создать опрос", callback_data="start_create")])
        kb.append([InlineKeyboardButton("📩 Мои опросы", callback_data="start_feedbacks")])

    markup = InlineKeyboardMarkup(kb)

    update.message.reply_text("Привет!", reply_markup=markup)

    return ConversationHandler.END


def help(update: Update, context: CallbackContext) -> int:
    msg = update.callback_query.message
    msg.edit_text("Сообщение помощь чо как делать все такое\n/start",
                  reply_markup=InlineKeyboardMarkup([]))
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
    context.user_data["feedback_name"] = txt

    try:
        transliterated = transliterate.translit(txt, reversed=True)
    except Exception:
        update.message.reply_text(
            "писать что ли не умеешь"
        )
        return CHOOSE_NAME

    if FeedbackMethods.name_exists(SessionLocal(), txt.lower()) is True:
        update.message.reply_text(
            "Такое есть уже лох"
        )
        return CHOOSE_NAME

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="create_back")],
    ])

    update.message.reply_text(
        f"пиши приветствие {transliterated}",
        reply_markup=markup
    )

    return CREATE_WELCOME


def create_welcome(update: Update, context: CallbackContext) -> int:
    name = context.user_data["feedback_name"]
    welcome_txt = update.message.text

    if name is None or welcome_txt is None:
        update.message.reply_text("хуита брат")
        return ConversationHandler.END

    welcome, url = FeedbackMethods.create_welcome(SessionLocal(), update.message.chat_id, name,
                                                  welcome_txt, update.message.bot.username)
    if welcome is None:
        update.message.reply_text("хуита брат")
        return ConversationHandler.END

    update.message.reply_photo(
        caption=f"Название опроса: {name}\n\n" + "ссылочку откройте молодой человек" +
                f"\n{f'https://t.me/{update.message.bot.username}?start={name}'}",
        photo=open(url, "rb")
    )

    return ConversationHandler.END


def my_feedbacks(update: Update, context: CallbackContext):
    msg = update.callback_query.message
    data = update.callback_query.data

    context.user_data["feedback_scroll_ids"] = [x.id for x in
                                                FeedbackMethods.get_welcomes(SessionLocal(), msg.chat_id)]

    if context.user_data.get("current_feedback_scroll_id") is None:
        context.user_data["current_feedback_scroll_id"] = 0
    else:
        if data == "feedback_scroll_left":
            context.user_data["current_feedback_scroll_id"] -= 1
            if context.user_data["current_feedback_scroll_id"] < 0:
                context.user_data["current_feedback_scroll_id"] = len(context.user_data["feedback_scroll_ids"]) - 1
        if data == "feedback_scroll_right":
            context.user_data["current_feedback_scroll_id"] += 1
            if len(context.user_data["feedback_scroll_ids"]) <= context.user_data["current_feedback_scroll_id"]:
                context.user_data["current_feedback_scroll_id"] = 0

    current_id = context.user_data["current_feedback_scroll_id"]
    msg = update.callback_query.message

    welcome_id = context.user_data["feedback_scroll_ids"][current_id]

    welcome = FeedbackMethods.get_welcome_by_id(SessionLocal(), welcome_id)

    kb = [
        [InlineKeyboardButton("⬅️", callback_data="feedback_scroll_left"),
         InlineKeyboardButton("➡️️", callback_data="feedback_scroll_right")]
    ]

    markup = InlineKeyboardMarkup(kb)

    try:
        msg.edit_media(media=InputMediaPhoto(
            media=open(welcome.code_url, 'rb'),
            caption=welcome.message + f"\n\n{welcome_id}"
        ), reply_markup=markup)
    except:
        msg.reply_photo(open(welcome.code_url, 'rb'), caption=welcome.message + f"\n\n{welcome_id}",
                        reply_markup=markup)


def main():
    models.Base.metadata.create_all(bind=engine)

    import os
    os.system("mkdir codes")

    updater = Updater(config.TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(help, pattern=r'start_help'))
    dp.add_handler(
        CallbackQueryHandler(my_feedbacks, pattern=r'^(?:start_feedbacks|feedback_scroll_left|feedback_scroll_right)$'))

    create = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_feedback, pattern=r'start_create')],
        states={
            CHOOSE_NAME: [MessageHandler(Filters.text & ~Filters.command, choose_name)],
            CREATE_WELCOME: [MessageHandler(Filters.text & ~Filters.command, create_welcome),
                             CallbackQueryHandler(create_feedback_back, pattern=r'create_back')],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True
    )

    dp.add_handler(create)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
