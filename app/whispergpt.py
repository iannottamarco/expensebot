import os
import json
import logging
from datetime import datetime
import openai
from openai import OpenAIError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_KEY'))

# Import local modules
from .categories import get_categories_and_id
from .expenses import add_expense


def openai_transcribe(path, user_id):
    """
    Transcribes an audio file using OpenAI's transcription service.

    Args:
        path (str): The path to the audio file to be transcribed.
        user_id (int): The ID of the user for logging purposes.

    Returns:
        The transcription result from OpenAI if successful, None otherwise.

    This function attempts to open and read the specified audio file, and then
    uses OpenAI's transcription service to transcribe it. It logs information
    about the transcription process, including successes and failures.
    """
    try:
        with open(path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            logging.info(f"User {user_id}: Successfully transcribed voice message.")
            return transcript
    except OpenAIError as oe:
        logging.error(f"User {user_id}: OpenAI transcription error: {oe}")
        return None
    except IOError as ioe:
        logging.error(f"User {user_id}: File I/O error: {ioe}")
        return None
    except Exception as e:
        logging.error(f"User {user_id}: General error in audio transcription: {e}")
        return None


def get_expensedata(user_id, textstring):
    """
    Retrieves expense data from a given text string using GPT-4.

    Args:
        user_id (int): The ID of the user for logging.
        textstring (str): The text string to be analyzed by the model.

    Returns:
        str: The JSON-formatted output from GPT-4 or an error message.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
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
        
        logging.info(f"User {user_id} expense info: {response.choices[0].message.content}")
        logging.info(f"API call for user {user_id} cost {response.usage.total_tokens} tokens.")
        
        output = str(response.choices[0].message.content)
        return output
    
    except OpenAIError as oe:
        logging.error(f"OpenAI chat completion error for user {user_id}: {oe}")
        return None
    
    except Exception as e:
        logging.error(f"Unexpected error for user {user_id}: {e}")
        return None
    

def parse_expense_json(json_output):
    """
    Parses a JSON string to extract expense details.

    Args:
        json_output (str): JSON-formatted string containing expense details.

    Returns:
        tuple: A tuple containing amount, category_id, description, date of the expense and error if present.
    """
    try:
        expense_json = json.loads(json_output)

        # Extract details from JSON
        exp_amount = expense_json.get('amount')
        exp_cat_id = expense_json.get('category_id')
        exp_description = expense_json.get('description')
        exp_date = expense_json.get('date')
        exp_error = expense_json.get('error')

        return exp_amount, exp_cat_id, exp_description, exp_date, exp_error

    except Exception as e:
        logging.error(f"Error parsing JSON {json_output} for expense data: {e}")
        return None