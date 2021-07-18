# created by RomaOkorosso at 18.07.2021
# texts.py
from commands import *

STR_ADMIN_HELP = f"""Чтобы создать опрос используйте кнопку в меню /{CMD_START}\n\n
Если у вас есть вопросы или предложения по работе бота, вы можете их отправить по \
<a href="https://t.me/asap_feedback_bot?start=asapteam_feedback_bot">ссылке</a> \
или написать в личные сообщения @mosenzova_iui\n\nСделано командой <a href="https://t.me/asapdvfu">ASAP❤️ </a>"""

STR_USER_HELP = (
    "Привет! Для того, чтобы оставить отзыв или задать вопрос, необходимо отсканировать QR-код."
    "Этот бот сделан для того, чтобы любой желающий мог просто, быстро и удобно оставить"
    "обратную связь на различные сервисы, предоставляемые университетом."
    " Сотрудники напрямую получат ваше обращение. Кстати, оно будет отправлено анонимно."
    " Если нужно, вы можете прикрепить к сообщению медиафайлы."
)

STR_INVALID_LINK = "неверная ссылка"
STR_ADMIN_WELCOME = "вы админ"

STR_FEEDBACK_COMPLAIN = "complain"
STR_FEEDBACK_SUGGEST = "suggest"
STR_FEEDBACK_PRAISE = "praise"
STR_FEEDBACK_ELSE = "else"

STR_WELCOME_TEXT = """
Опрос: {name}

Приветствие:
{message}
"""

STR_START_MSG = "Привет!"
STR_START_HELP = "🙋 Помощь"
STR_START_HISTORY = "💬 Мои ответы"
STR_START_CREATE_WELCOME = "✉️ Создать опрос"
STR_START_ME_WELCOMES = "📩 Мои опросы"
STR_SHARE_ADMIN = "!Дать админку другому челу!"

STR_CANCEL = "Отменить"
STR_BACK = "⬅️ Назад"
STR_ERROR = "Ошибочка вышла"

STR_YOUR_TOKEN = "ссылка для нового админа: {token}"

STR_NEW_WELCOME_NAME = "название опроса"
STR_INVALID_WELCOME_NAME = "писать что ли не умеешь"
STR_WELCOME_NAME_TAKEN = "Такое название уже есть"
STR_NEW_WELCOME_MESSAGE = "пиши приветствие"
STR_WELCOME_OVERVIEW = """
Название опроса: {name}
Приветствие: {message}
Ссылка: {link}
"""
STR_NO_WELCOMES = "Пока опросом немае"
STR_WELCOME_EDIT_TITLE = "edit title (you will need to edit qr codes)"
STR_WELCOME_EDIT_DESCRIPTION = "edit description"
STR_WELCOME_WHAT_TO_EDIT = "чо редачить"
STR_WELCOME_NEW_TITLE = "new title"
STR_WELCOME_NEW_DESCRPTION = "new desc"
STR_WELCOME_TITLE_EDITED = "title edited!"
STR_WELCOME_DESC_EDITED = "desc edited!"
STR_WELCOME_DELETED = "DELETED"
STR_DELETE_ASK = "Точно удалить?"
STR_YES = "Да"
STR_NO = "Нет"

STR_ARROW_LEFT = "⬅️"
STR_ARROW_RIGHT = "➡️️"
STR_WELCOME_EDIT = "Edit"
STR_WELCOME_DELETE = "delete"


STR_FEEDBACK_REPLY = """
Вам ответили по вашему обращению по опросу: {name}
{message}
"""
