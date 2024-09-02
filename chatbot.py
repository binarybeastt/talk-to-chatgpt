import google.generativeai as genai
import os

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

with open('chatbot1.txt', 'r', encoding='utf-8') as infile:
    system_instruction = infile.read()

def init_chat():
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
    chat = model.start_chat(
        history=[
            {"role": "user", "parts": "Hello"},
            {"role": "model", "parts": "Let's go on with the conversation"},
        ]
    )
    return chat

async def get_response(chat, user_input):
    response = chat.send_message(user_input)
    return response.text
