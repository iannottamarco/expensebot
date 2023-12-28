import logging
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters, CallbackQueryHandler
)
# Import Functions
from app.users import is_user_registered, create_user
from app.categories import add_category, generate_categories_message, get_categories_and_id, change_category_status, get_category_name
from app.gsheet import add_basicinfo, extract_spreadsheet_id, get_google_auth_url
from app.expenses import add_expense, retrieve_last_expense_id, delete_expense
from app.whispergpt import openai_transcribe, get_expensedata, add_expense_from_json, parse_expense_json

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

#####################
## FLASK
from app.flask_app import app as flask_app
from threading import Thread

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
            [InlineKeyboardButton("📞 Get Support",url= 'https://t.me/fratebanca')],
            [InlineKeyboardButton("☕️ Buy me a Coffee",url= 'https://www.buymeacoffee.com/marcoiannotta')],
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
## VOICE EXPENSE
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_user_registered(user_id):
        try:
            user_id = update.effective_user.id
            path = f"audio/{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.ogg"
            voice_message = update.message.voice
            voice_file = await context.bot.get_file(voice_message.file_id)

            # Correctly using the download method
            await voice_file.download_to_drive(custom_path=path)

            # Transcribe
            testo = openai_transcribe(path, user_id).text
            # Get infor from text
            outputgpt = get_expensedata(user_id, testo)

            exp_amount, exp_cat_id, exp_description, exp_date, exp_error = parse_expense_json(outputgpt)

            if exp_error:
                await update.message.reply_text(exp_error)

            else:
            # Add expense
                add_expense(user_id=user_id, amount=exp_amount, category_id=exp_cat_id, date=exp_date, description=exp_description)
                catname = get_category_name(user_id=user_id,category_id=exp_cat_id)
                expense_id = retrieve_last_expense_id(user_id)

                # Create an inline keyboard with a button to delete the expense
                keyboard = [
                    [InlineKeyboardButton("❌Delete Expense", callback_data=f'deleteexpense_{expense_id}')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(f"Expense added! Here are the info:\n 💶Amount: {exp_amount}€\n 🗂Category: {catname}\n 📅Date: {exp_date}\n 📃Description: {exp_description}",reply_markup=reply_markup)

            
        except Exception as e:
            print(f"Error: {e}")
            await update.message.reply_text("There was an error processing your voice message.")
    else:
        # Respond to unregistered users
        await update.message.reply_text("Please register to use this feature.")


async def handle_expense_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith('deleteexpense_'):
        expense_id = int(data.split('_')[1])
        success = delete_expense(user_id, expense_id)
        # Prepare response based on the operation success
        if success:
            response_message = "Expense deleted successfully. Add a new expense manually or send a voice message."
        else:
            response_message = "Failed to delete the expense."

        await query.edit_message_text(text=response_message)

    else:
        logging.error(f"There was an error deleting the expense {expense_id} of user {user_id}")
        await query.edit_message_text(text="There was an error deleting your expense.")


######################
## ADD EXPENSE
EXPENSE_AMOUNT, EXPENSE_CATEGORY, EXPENSE_DESCRIPTION, EXPENSE_DATE = range(4)

async def start_expensecreation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await ask_expenseamount(update, context)

async def ask_expenseamount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    logger.info(f"Received callback query for expense amount from user: {query.from_user.id}")
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        'Please enter your expense amount: (for decimal use ".", comma separator will soon be implemented.)', 
        reply_markup=reply_markup
    )
    logger.info("Asking user for their expense amount")

    return EXPENSE_AMOUNT

async def ask_expensecategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    context.user_data['expense_amount'] = update.message.text
    user_id = update.message.from_user.id
    
    # Fetch categories and their IDs
    categories = get_categories_and_id(user_id, 1)

    # Create inline keyboard buttons for each category
    keyboard_buttons = [
        [InlineKeyboardButton(category[0], callback_data=f"expensecat_{category[1]}")]
        for category in categories
    ]

    # Add 'Cancel' button
    keyboard_buttons.append([InlineKeyboardButton("⬅️ Cancel", callback_data='cancel')])

    # Create InlineKeyboardMarkup
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    # Send the message with inline keyboard
    await update.message.reply_text(
        "Select the category of the expense:",
        reply_markup=reply_markup
    )

    return EXPENSE_CATEGORY  # Assuming the next state is EXPENSE_DATE

async def ask_expensedescription(update: Update, context: ContextTypes.DEFAULT_TYPE):
     # This function is expected to be triggered after choosing a category, which is a callback query
    query = update.callback_query
    await query.answer()    

    category_id = query.data.split('_')[1]
    context.user_data['expense_category_id'] = category_id

    logger.info(f"Received callback query for expense amount from user: {query.from_user.id}")
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        'Please enter your expense description:', 
        reply_markup=reply_markup
    )
    logger.info("Asking user for their expense description")

    return EXPENSE_DESCRIPTION


async def ask_expensedate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    context.user_data['expense_desription'] = update.message.text

    # Define date options
    dates = [
        ("📅 Today", datetime.now().strftime("%Y-%m-%d")),
        ("🗓 Yesterday", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")),
        ("🗓 Day Before Yesterday", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"))
    ]

    # Create keyboard buttons for each date option
    keyboard_buttons = [
        [InlineKeyboardButton(date_label, callback_data=f"date_{date_str}")]
        for date_label, date_str in dates
    ]

    # Add 'Cancel' button
    keyboard_buttons.append([InlineKeyboardButton("⬅️ Cancel", callback_data='cancel')])

    # Create InlineKeyboardMarkup
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

     # Send the message with inline keyboard
    await update.message.reply_text(
        "Select the date:",
        reply_markup=reply_markup
    )

    # # Send the message with inline keyboard
    # await query.message.reply_text(
    #     "Select the date:",
    #     reply_markup=reply_markup
    # )

    # print(query.data)

    return EXPENSE_DATE


async def complete_expensecreation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    await query.answer()
    print(query.data)
    # Assuming the callback data is the date or an identifier for the date
    exp_date = query.data.split('_')[1]
    context.user_data['expense_date'] = exp_date

    user_id = update.effective_user.id
    print(user_id)
    expense_amount = context.user_data.get('expense_amount')
    print(expense_amount)
    expense_category_id = context.user_data.get('expense_category_id')
    print(expense_category_id)
    expense_description = context.user_data.get('expense_description')
    print(expense_description)
    expense_date = context.user_data.get('expense_date')
    print(expense_date)

    # Validate the data and add the expense (validation and error handling not shown here)
    try:
        add_expense(user_id=user_id, amount=expense_amount, date=expense_date, category_id=expense_category_id, description=expense_description)
        expense_id = retrieve_last_expense_id(user_id)
        keyboard = [
                [InlineKeyboardButton("❌Delete Expense", callback_data=f'deleteexpense_{expense_id}')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Confirmation message to the user
        catname = get_category_name(user_id=user_id,category_id=expense_category_id)

        await query.message.reply_text(f"Expense added! Here are the info:\n 💶Amount: {expense_amount}€\n 🗂Category: {catname}\n 📅Date: {expense_date}\n 📃Description: {expense_description}",reply_markup=reply_markup)
        

    except:
        await query.message.reply_text("There was an error adding your expense.")

    return ConversationHandler.END



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


async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if 'email' key is already in user_data, which means this function has been called before
    if 'email' in context.user_data:
        user_input = update.message.text
        context.user_data['email'] = user_input
        
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
    await update.message.reply_text('Registration complete, go back to the home /start')
    return ConversationHandler.END

######################
## GET SPREADSHEET_ID
SPREADSHEET_ID, SHEET_NAME = range(2)

async def get_spreadsheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await ask_spreadsheetid(update, context)

async def ask_spreadsheetid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    logger.info(f"Received callback query for spreadsheet_id from user: {query.from_user.id}")
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text('Please enter your Google Sheet link:', reply_markup=reply_markup)
    logger.info("Asking user for their spreadsheet_id")

    return SPREADSHEET_ID

async def ask_sheetname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    extracted_id = extract_spreadsheet_id(update.message.text)

    if extracted_id is None:
        await update.message.reply_text("The spreadsheet ID is not valid. Please /start again and provide a valid Google Sheets link or ID.")
        return ConversationHandler.END  # Ends the conversation
    else:
        context.user_data['spreadsheet_id'] = extracted_id

    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('How would you like to call the sheet containing the rawdata? (Max 15 characters)', reply_markup=reply_markup)

    return SHEET_NAME

async def complete_spreadsheetcreation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['spreadsheet_name'] = update.message.text

    if len(update.message.text) > 15:
        await update.message.reply_text('The name should be no more than 15 characters. Please try again.')
        return SHEET_NAME
    
    user_id = update.effective_user.id
    spreadsheet_id = context.user_data.get('spreadsheet_id')
    sheet_name = context.user_data.get('sheet_name')

    add_basicinfo(user_id,spreadsheet_id,sheet_name)
    authurl = get_google_auth_url()

    await update.message.reply_text(f'Grant the bot access using this link {authurl}')

    return ConversationHandler.END

######################
## CANCEL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the conversation from the user."""
    await update.message.reply_text('Conversation cancelled. Type /start to begin again.')
    return ConversationHandler.END

#####################
## BOT HANDLERS

def run_bot():
    application = ApplicationBuilder().token(API_KEY).build()

    ## COMMANDS
    #START
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    #NEW EXPENSE
    newexpense_handler = CommandHandler('newexpense', start_expensecreation)
    application.add_handler(newexpense_handler)


    ## AUDIO HANDLER
    voice_handler = MessageHandler(filters.VOICE, handle_voice_message)
    application.add_handler(voice_handler)

    expense_delete_handler = CallbackQueryHandler(handle_expense_delete, pattern='^deleteexpense_')
    application.add_handler(expense_delete_handler)

    ## ADD EXPENSE FLOW
    newexpense_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_expensecreation, pattern='^add_expense$')],
    states={
        EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_expensecategory)],
        EXPENSE_CATEGORY: [CallbackQueryHandler(ask_expensedescription, pattern='^expensecat_')],
        EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_expensedate)],
        EXPENSE_DATE: [CallbackQueryHandler(complete_expensecreation, pattern='^date_')]
    },
    fallbacks=[CallbackQueryHandler(cancel_registration, pattern='^cancel$')],
    per_message=False
    )
    application.add_handler(newexpense_conv_handler)


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

    ## SPREADSHEET SETUP
    spreadsheet_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler( get_spreadsheet,pattern = '^connect_gsheet$')],
        states = {
            SPREADSHEET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sheetname)],
            SHEET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, complete_spreadsheetcreation)]
        },
        fallbacks=[CallbackQueryHandler(cancel_registration, pattern='^cancel$')],
        per_message=False
    )
    application.add_handler(spreadsheet_conv_handler)

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


if __name__ == '__main__':

    # Run bot in separate thread
    Thread(target=run_bot()).start()
    # Run flask in main thread
    flask_app.run(port=5000)