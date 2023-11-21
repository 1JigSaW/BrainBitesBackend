import os

from openai import OpenAI
print(os.environ.get('OPENAI_API'))
client = OpenAI(api_key=os.environ.get('OPENAI_API'))
print(client)
from django.core.management.base import BaseCommand
from app.models import Topic, Subtitle


def create_cards_with_quizzes(topic_id, subtitle_id):
    # Set the API key from Django settings
    

    # Retrieve the topic and subtitle from the database
    topic = Topic.objects.get(id=topic_id)
    subtitle = Subtitle.objects.get(id=subtitle_id)
    print(topic, subtitle)

    # Formulate the prompt
    prompt = f'''
            Смотри у меня приложение которое будет давать людям изучать краточки с полезными заниями.
            Можешь написать 5 карточек по теме {topic.title} и по подтеме {subtitle.title} это в json где основной контент не 
            занимал более 770 символов с пробелами. JSON структура такая 
            {{"card": {{"title": "Название картчоки", "content": "Основной текст", "source": "Источник"}},
            "quiz": {{"question": 
            "Сам вопрос квиза", "answers": ["Варианты ответов в массиве"], "correct_answer": "Правильный ответ"}}}}
            Не пиши лишний текст, только json, никаких комментариев от тебя, а то я не смогу принять ответ.
            '''
    print(prompt)
    # Make the API call
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        print(response)

        # Get the response content
        response_content = response.choices[0].message['content']
        print(response_content)
        # Here, you can further process response_content to save it into your Cards model
        # ...

        return response_content
    except Exception as e:
        print(f"Error: {e}")
        return None


class Command(BaseCommand):
    help = 'Описание вашей команды'

    def handle(self, *args, **kwargs):
        # Ваш код здесь
        # Например, вызов функции для создания карточек
        result = create_cards_with_quizzes(1, 2)
        self.stdout.write(self.style.SUCCESS(f'Успешно выполнено: {result}'))
