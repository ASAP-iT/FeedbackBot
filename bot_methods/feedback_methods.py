# feedback_methods.py
# FeedbackBot
# Created by romanesin on 18.07.2021


SELECT_TYPE, FEEDBACK, WANTS_REPLY = range(3)


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