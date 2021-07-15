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


def main():
    models.Base.metadata.create_all(bind=engine)

    import os
    os.system("mkdir codes")

    updater = Updater(config.TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(help, pattern=r'start_help'))

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
