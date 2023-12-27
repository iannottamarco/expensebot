from .categories import get_categories_and_id
from .expenses import add_expense

import os 
import json
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

from datetime import datetime
import openai
client = openai.OpenAI(api_key=os.getenv('OPENAI_KEY'))



def openai_transcribe(path,user_id):
    try:
        with open(path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1",
                                                            file= audio_file)
            logging.info(f"Transcribed {user_id} voice message: {transcript}")
            return transcript
    except Exception as e:
        logging.error(f"{user_id} audio transcription not possible for: {e}")


def get_expensedata(user_id, textstring):
    today = datetime.utcnow()
    user_categories = get_categories_and_id(user_id, type=1)

    system_message = {
        "role": "system",
        "content": f"You are a budget assistant. Extract expense information from the user's input and respond with the details in JSON format.\
        These are the user categories: {user_categories}\
        Include 'amount':value of the expense (decimal),\
            'category_id': category unique identifier (integer),\
            'category_name': the category name (string),\
            'description': brief description of the expense (string),\
            'date': today is {today}, if not specified set today (YYYY-MM-DD format),\
             and 'error': use this field whenever you are not certain about one of the responses above, insert suggestions for user. (string).\
        If you are not certain about any of the fields use None and valorize the 'error' field. Give detailed suggestions based on user laguage."
    }

    user_message = {
        "role": "user",
        "content": textstring
    }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[system_message, user_message],
            response_format={"type": "json_object"}  # Setting the response format to JSON
        )
        
        logging.info(f"{user_id} expense info are {response.choices[0].message.content}")
        logging.info(f"API call for user {user_id} costed {response.usage.total_tokens} tokens.")
        
        output = response.choices[0].message.content
        output = str(output)
        return output
    
    except Exception as e:
        logging.error(f"Error in getting expense data for: {e}")


def add_expense_from_json(user_id, json_output):
    try:
        expense_json = json.loads(json_output)

        if expense_json['error'] is None:
            exp_user_id = user_id
            exp_amount = expense_json['amount']
            exp_cat_id = expense_json['category_id']
            exp_cat_name = expense_json['category_name']
            exp_description = expense_json['description']
            exp_date = expense_json['date']

        else:
            return expense_json['error']
        
    except Exception as e:
        logging.error(f"Wasn't able to convert string to json for {e}")

    try:
        add_expense(user_id=exp_user_id, amount=exp_amount, category_id=exp_cat_id, description=exp_description, date=exp_date)

        return f"Expense added! Here are the info:\n 💶Amount: {exp_amount}€\n 🗂Category: {exp_cat_name}\n 📅Date: {exp_date}\n 📃Description: {exp_description}"
    
    except Exception as e:
        logging.error(f"Error in adding expense to the db for {e}")
        return e