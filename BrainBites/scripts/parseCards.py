import os
import sys
import django
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('OPENAI_API'))

# Determine the absolute path to the settings module
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
settings_path = os.path.join(project_dir, 'BrainBites', 'settings')

# Add the project directory to sys.path
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BrainBites.settings')
sys.path.insert(0, settings_path)

import django
django.setup()

# Now you can import your Django models
from app.models import Topic, Subtitle

# Rest of your script...



# Function to get GPT response and save it for a topic and subtitle
def create_cards_with_quizzes(topic_id, subtitle_id):
    # Set the API key from Django settings
    

    # Retrieve the topic and subtitle from the database
    topic = Topic.objects.get(id=topic_id)
    subtitle = Subtitle.objects.get(id=subtitle_id)

    # Formulate the prompt
    prompt = f'''
    Смотри у меня приложение которое будет давать людям изучать краточки с полезными заниями.
    Можешь написать 5 карточек по теме {topic.name} и по подтеме {subtitle.title} это в json где основной контент не 
    занимал более 770 символов с пробелами. JSON структура такая 
    {"card": {"title": "Название картчоки", "content": "Основной текст", "source": "Источник"},
    "quiz": {"question": 
    "Сам вопрос квиза", "answers": ["Варианты ответов в массиве"], "correct_answer": "Правильный ответ"}}
    Не пиши лишний текст, только json, никаких комментариев от тебя, а то я не смогу принять ответ.
    '''

    # Make the API call
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "You are a knowledgeable assistant."},
            {"role": "user", "content": prompt}
        ])

        # Get the response content
        response_content = response.choices[0].message['content']

        # Here, you can further process response_content to save it into your Cards model
        # ...

        return response_content
    except Exception as e:
        print(f"Error: {e}")
        return None


create_cards_with_quizzes(1, 2)