from .categories import get_categories_and_id

import os 
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(filename='./logs/mylogs.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

from datetime import datetime
from pydub import AudioSegment
import openai
client = openai.OpenAI(api_key=os.getenv('OPENAI_KEY'))


def check_lenght(path):
    try:
        audio = AudioSegment.from_file(path)
        duration = len(audio) / 1000.0
        return round(duration,1)
    except Exception as e:
        logging.info(f"Audio duration retrieval not possible for: {e}")
        return None


def openai_transcribe(path):
    try:
        with open('audiotest/WhatsApp Ptt 2023-12-07 at 08.56.50.ogg', 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1",
                                                            file= audio_file)
            return transcript
    except Exception as e:
        logging.info(f"Audio transcription not possible for: {e}")

def get_info_from_text(user_id, textstring):
    today = datetime.utcnow()
    categories = get_categories_and_id(user_id, type = 1)

    system_message = {
        "role":"system",
        "content": f"""
        You are a bot that extract customer expense data from phrases. You need to extract: amount, category and date.
        Amount: is a number, might be decimal.
        Category needs to be picked among these: {categories}, if yo do not find a matching category use None object.
        Date: today is {today}, if not specified is {today}. Format needs to be year - month - day

        The output must(!) be a list with three objects: amount, category and date. Like this:
        [26, "Birre","2023-12-07"]
        
    """
    }

    user_message = {
        "role":"user",
        "content": textstring
    }

    response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[system_message, user_message],
    max_tokens=3800
)

    answer_gpt = response.choices[0].message.content
    print(answer_gpt)
    return answer_gpt

get_info_from_text(17073726,"Ciao oggi ho speso 26 euro in bici")


# def audio_handler(path):
#     if check_lenght(path) < 15:
#         audio_text = openai_transcribe(path)
#     else:
#         return "Voice message is too long, it should be under 15 seconds."