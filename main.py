##### INITIAL SETUP #####
import logging
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
load_dotenv()
import auth


## Setup logging
logging.basicConfig(filename='mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)

## CODE BELOW TO BE REVIEWED ##

# User states
USER_STATE = {}  # Stores the state of each user

# Check state of the user in the Flow
def get_user_state(user_id):
    logging.debug(f'[{user_id}] This user state is {USER_STATE}')
    return USER_STATE.get(user_id, None)

# Set state of user in the Flow
def set_user_state(user_id, state):
    logging.info(f'[{user_id}] This user state is {state}')
    USER_STATE[user_id] = state


####### FIRST MESSAGE HANDLER #######
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id

    if not auth.is_user_registered(user_id):
        current_state = get_user_state(user_id)

        if current_state is None:
            set_user_state(user_id, 'ask_name')
            bot.send_message(message.chat.id, "Welcome, please enter your name.")
            logging.debug(f'[{user_id}] is now {USER_STATE}')

        elif current_state == 'ask_name':
            set_user_state(user_id, 'ask_surname')
            # Store the name temporarily
            USER_STATE[str(user_id) + '_name'] = message.text
            bot.send_message(message.chat.id, "Please enter your surname.")
            logging.debug(f'[{user_id}] is now {USER_STATE}')

        elif current_state == 'ask_surname':
            # Retrieve the stored name
            name = USER_STATE.pop(str(user_id) + '_name')
            surname = message.text

            # Register the user
            auth.register_user(user_id, name, surname)
            set_user_state(user_id, None)  # Reset the state
            bot.send_message(message.chat.id, "Registration successful.")
            logging.debug(f'[{user_id}] is now {USER_STATE}')
    else:
        echo_all(message)


def handle_add_expense(call):
    # Logic for adding an expense
    bot.answer_callback_query(call.id, "Adding an expense...")

def handle_delete_last_expense(call):
    # Logic for deleting the last expense
    bot.answer_callback_query(call.id, "Deleting last expense...")

def handle_get_statistics(call):
    # Logic for getting statistics
    bot.answer_callback_query(call.id, "Fetching statistics...")

callback_handlers = {
    "add_expense": handle_add_expense,
    "delete_last_expense": handle_delete_last_expense,
    "get_statistics": handle_get_statistics,
}

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    handler = callback_handlers.get(call.data)
    if handler:
        handler(call)


def get_main_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Add an expense", callback_data="add_expense"),
               InlineKeyboardButton("Delete last expense", callback_data="delete_last_expense"),
               InlineKeyboardButton("Get statistics", callback_data="get_statistics"))
    return markup


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    markup = get_main_menu_markup()
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)


def safe_callback(handler):
    def wrapped_handler(call):
        try:
            handler(call)
        except Exception as e:
            logging.error(f"Error in callback handler: {e}")
            # Respond to the user with a friendly error message if needed
    return wrapped_handler

# Apply this wrapper to your callback handlers




bot.polling()