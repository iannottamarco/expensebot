import logging
import re
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters, CallbackQueryHandler
)
# Import Functions
from app.users import is_user_registered, create_user
from app.categories import add_category, generate_categories_message, get_categories_and_id, change_category_status

## Setup logging
logging.basicConfig(
    filename='logs/mylogs.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

## Create bot
load_dotenv()
API_KEY = os.getenv('API_KEY')




######################
## START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_user_registered(user_id):
        logger.info(f"Registered user {user_id} started the bot")
        # Display a welcome back message with inline buttons for registered users
        keyboard = [
            [InlineKeyboardButton("💸 Add an Expense", callback_data='add_expense')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='user_settings')],
            [InlineKeyboardButton("🌐 GitHub Repository", url='https://github.com/iannottamarco/expensebot')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user_id, 
            text="Welcome back! How can I assist you today?",
            reply_markup=reply_markup
        )

    else:
        logger.info(f"Unregistered user {user_id} started the bot")
        # Display a welcome message with inline buttons for unregistered users
        keyboard = [
            [InlineKeyboardButton("📝 Register", callback_data='register_user')],
            [InlineKeyboardButton("🌐 GitHub Repository", url='https://github.com/iannottamarco/expensebot')],
            [InlineKeyboardButton("📞 Get Support",url= 'https://t.me/fratebanca')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user_id, 
            text="👋 Welcome to @amibrokepybot, the bot that helps you quickly track your expenses 💸. Get started now and take control of your financial health! 📊",
            reply_markup=reply_markup
        )


######################
## SETTINGS
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🗂️ Manage Categories", callback_data='manage_categories')], #List categories, Add category, Deactivate category, Reactivate category
        [InlineKeyboardButton("❌ Delete an Expense", callback_data='delete_expense')], # Delete an expense by id
        [InlineKeyboardButton("🔗 GSheet Settings", callback_data='connect_gsheet')], #Link GSheet, Change Gsheet, Push all past data to Gsheet
        [InlineKeyboardButton("📥 Export CSV", callback_data='export_csv')], #Send csv to chat
        [InlineKeyboardButton("👤 User Settings", callback_data='export_csv')], # Modify email, Delete account
        [InlineKeyboardButton("⬅️ Go Back", callback_data='go_backhome')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Settings: Choose an option",
        reply_markup=reply_markup
    )


######################
## GO BACK HOME
async def go_backhome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Call the start function to display the main menu
    await start(update, context) 

######################
## CATEGORIES SETTINGS
async def show_cat_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ Add a new category", callback_data='add_category')],
        [InlineKeyboardButton("📋 List all categories", callback_data='list_categories')],
        [InlineKeyboardButton("🚫 Deactivate category", callback_data='deactivate_category')],
        [InlineKeyboardButton("✅ Reactivate category", callback_data='reactivate_category')],
        [InlineKeyboardButton("⬅️ Go Back", callback_data='go_backhome')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_reply_markup(reply_markup=reply_markup)


######################
## ADD NEW CATEGORY
CATEGORY_NAME, CATEGORY_DESCRIPTION = range(2)

async def start_categorycreation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await ask_categoryname(update, context)

async def ask_categoryname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    logger.info(f"Received callback query for category name from user: {query.from_user.id}")
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text('Please enter your category name:', reply_markup=reply_markup)
    logger.info("Asking user for their category name")

    return CATEGORY_NAME

async def ask_categorydescription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category_name'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please enter a description:', reply_markup=reply_markup)
    
    return CATEGORY_DESCRIPTION

async def complete_categorycreation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category_description'] = update.message.text

    user_id = update.effective_user.id
    category_name = context.user_data.get('category_name')
    category_description = context.user_data.get('category_description')

    add_category(user_id,category_name,category_description)

    await update.message.reply_text('Category created! Go back to /start')

    return ConversationHandler.END

######################
## DEACTIVATE CATEGORY
async def send_inactive_category_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Fetch categories and their IDs
    categories = get_categories_and_id(user_id, 1)  # 1 for active categories

    # Create inline keyboard buttons for each category
    keyboard_buttons = [
        [InlineKeyboardButton(category[0], callback_data=f"deactivate_{category[1]}")]
        for category in categories
    ]

    # Add 'Cancel' button
    keyboard_buttons.append([InlineKeyboardButton("⬅️ Cancel", callback_data='cancel')])

    # Create InlineKeyboardMarkup
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    # Send the message with inline keyboard
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Select the category you want to deactivate",
        reply_markup=reply_markup
    )

async def handle_category_deactivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith('deactivate_'):
        category_id = int(data.split('_')[1])
        success = change_category_status(user_id, category_id, False)
        # Prepare response based on the operation success
        if success:
            response_message = "Category deactivated successfully."
        else:
            response_message = "Failed to deactivate the category."

        await query.edit_message_text(text=response_message)
    elif data == 'cancel':
        await query.edit_message_text(text="Operation cancelled.")
    
    asyncio.sleep(1.2)
    await show_cat_setting(update, context)

######################
## REACTIVATE CATEGORY
async def send_active_category_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Fetch categories and their IDs
    categories = get_categories_and_id(user_id, 2)  # 2 for inactive categories

    # Create inline keyboard buttons for each category
    keyboard_buttons = [
        [InlineKeyboardButton(category[0], callback_data=f"reactivate_{category[1]}")]
        for category in categories
    ]

    # Add 'Cancel' button
    keyboard_buttons.append([InlineKeyboardButton("⬅️ Cancel", callback_data='cancel')])

    # Create InlineKeyboardMarkup
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    # Send the message with inline keyboard
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Select the category you want to reactivate",
        reply_markup=reply_markup
    )

async def handle_category_reactivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith('reactivate_'):
        category_id = int(data.split('_')[1])
        success = change_category_status(user_id, category_id, True)
        # Prepare response based on the operation success
        if success:
            response_message = "Category re-activated successfully."
        else:
            response_message = "Failed to re-activate the category."

        await query.edit_message_text(text=response_message)
    elif data == 'cancel':
        await query.edit_message_text(text="Operation cancelled.")
    
    asyncio.sleep(1.2)
    await show_cat_setting(update, context)


######################
## LIST CATEGORIES
async def list_categories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    categories_message = generate_categories_message(user_id)

    keyboard = [
        [InlineKeyboardButton("⬅️ Go Back", callback_data='go_backhome')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message
    await context.bot.send_message(chat_id=query.message.chat_id, text=categories_message, reply_markup=reply_markup)


######################
## REGISTER
# Define conversation states
FIRST_NAME, LAST_NAME, EMAIL, CANCEL = range(4)

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await ask_first_name(update, context)


async def ask_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    logger.info(f"Received callback query for first name from user: {query.from_user.id}")
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text('Please enter your first name (optional):', reply_markup=reply_markup)
    logger.info("Asking user for their first name")

    return FIRST_NAME


async def ask_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please enter your last name (optional):', reply_markup=reply_markup)
    
    return LAST_NAME

import re
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9.-]{3,}\.(com|org|net|edu|gov|mil|co|uk|us|info|it|es|eu|fr)\b'

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if 'email' key is already in user_data, which means this function has been called before
    if 'email' in context.user_data:
        user_input = update.message.text

        if re.fullmatch(EMAIL_REGEX, user_input):
            context.user_data['email'] = user_input
            # Proceed to the next step of your bot's logic
            # For example, return NEXT_STATE
        else:
            # If the input is not a valid email, ask again
            await update.message.reply_text('Invalid email format. Please enter a valid email:')
            return EMAIL
    else:
        # Store the last name from the previous step
        context.user_data['last_name'] = update.message.text

        # Prompt the user to enter their email
        keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please enter your email:', reply_markup=reply_markup)
        
        # Set a flag indicating that the email prompt has been shown
        context.user_data['email'] = None
        return EMAIL


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Process cancelled /start again the bot.")
    # Resetting the user data if any was stored
    context.user_data.clear()
    # Redirect the user back to the homepage
    start(update, context)
    return ConversationHandler.END  # This line is crucial to reset the conversation state



async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    email = context.user_data.get('email')
    first_name = context.user_data.get('first_name')
    last_name = context.user_data.get('last_name')

    create_user(email, user_id, chat_id, first_name, last_name)
    await update.message.reply_text('Registration complete!')
    return ConversationHandler.END


######################
## CANCEL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the conversation from the user."""
    await update.message.reply_text('Conversation cancelled. Type /start to begin again.')
    return ConversationHandler.END



if __name__ == '__main__':
    application = ApplicationBuilder().token(API_KEY).build()

    #START
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    ## REGISTRATION FLOW
    registration_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_registration, pattern='^register_user$')],
    states={
        FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_last_name)],
        LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],       
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, complete_registration)],
        CANCEL: [CallbackQueryHandler(cancel_registration, pattern='^cancel$')]
    },
    fallbacks=[CallbackQueryHandler(cancel_registration, pattern='^cancel$')],
    per_message=False  # Changed to False
    )
    application.add_handler(registration_conv_handler)

    ## SETTINGS
    settings_handler = CallbackQueryHandler(show_settings, pattern='^user_settings$')
    application.add_handler(settings_handler)

    ## CATEGORY SETTINGS
    cat_settings_handler = CallbackQueryHandler(show_cat_setting, pattern='^manage_categories$')
    application.add_handler(cat_settings_handler)

    ## LIST CATEGORY
    cat_settings_handler = CallbackQueryHandler(list_categories_handler, pattern='^list_categories$')
    application.add_handler(cat_settings_handler)

    ## NEW CATEGORY FLOW
    newcat_conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_categorycreation,pattern='^add_category$')],
        states={
            CATEGORY_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_categorydescription)],
            CATEGORY_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, complete_categorycreation)]
        },
        fallbacks=[CallbackQueryHandler(cancel_registration, pattern='^cancel$')],
        per_message=False
    )
    application.add_handler(newcat_conversation_handler)

    ## DEACTIVATE CATEGORY
    category_deactivation_begin = CallbackQueryHandler(send_inactive_category_list, pattern='deactivate_category')
    application.add_handler(category_deactivation_begin)

    category_deactivation_handler = CallbackQueryHandler(handle_category_deactivation, pattern='^deactivate_')
    application.add_handler(category_deactivation_handler)

    ## ACTIVATE CATEGORY
    category_reactivation_begin = CallbackQueryHandler(send_active_category_list, pattern='reactivate_category')
    application.add_handler(category_reactivation_begin)

    category_reactivation_handler = CallbackQueryHandler(handle_category_reactivation, pattern='^reactivate_')
    application.add_handler(category_reactivation_handler)

    ## BACK HOME
    go_backhome_handler = CallbackQueryHandler(go_backhome, pattern='^go_backhome$')
    application.add_handler(go_backhome_handler)

    # Start the bot
    application.run_polling()
