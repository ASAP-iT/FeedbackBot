# created by RomaOkorosso at 18.07.2021
# commands.py

CMD_START = "start"
CMD_CANCEL = "cancel"
CMD_HELP = "help"
CMD_ADMIN = "share_admin"

CALLBACK_HELP = "start_help"
CALLBACK_GRANT_ADMIN = "start_grand_admin"
CALLBACK_SELECT_TYPE = "^(?:complain|suggest|praise|else)$"
CALLBACK_WANTS_REPLY = "^(?:yes|no|prev_menu)$"
CALLBACK_REPLY_FEEDBACK = "reply_to_feedback-*"
CALLBACK_MY_FEEDBACKS = (
    "^(?:start_feedbacks|feedback_scroll_left|feedback_scroll_right)$"
)
CALLBACK_MY_HISTORY = "^(?:start_history|history_scroll_left|history_scroll_right)$"
CALLBACK_WELCOME_EDIT = "welcome_edit-*"
CALLBACK_DELETE = "edit_welcome_delete-*"
CALLBACK_WELCOME_BACK = "edit_welcome_back"
CALLBACK_EDIT_WELCOME_TITLE = "edit_welcome_title-*"
CALLBACK_EDIT_WELCOME_DESCRIPTION = "edit_welcome_description-*"
CALLBACK_YES = "yes"
CALLBACK_NO = "no"
CALLBACK_WELCOME_BACK_NO = "^(?:no|edit_welcome_back)$"
CALLBACK_CREATE = "start_create"
CALLBACK_CREATE_BACK = "create_back"
CALLBACK_PREV_MENU = "prev_menu"
CALLBACK_FEEDBACK_LEFT = "feedback_scroll_left"
CALLBACK_FEEDBACK_RIGHT = "feedback_scroll_right"
CALLBACK_HISTORY_LEFT = "history_scroll_left"
CALLBACK_HISTORY_RIGHT = "history_scroll_right"
CALLBACK_HISTORY_FEEDBACKS = (
    "^(?:his_feedbacks|his_feedbacks_left|his_feedbacks_right)$"
)
CALLBACK_HISTORY_FEED_LEFT = "his_feedbacks_left"
CALLBACK_HISTORY_FEED_RIGHT = "his_feedbacks_right"
