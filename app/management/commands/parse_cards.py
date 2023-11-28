import os

from openai import OpenAI
print(os.environ.get('OPENAI_API'))
client = OpenAI(api_key=os.environ.get('OPENAI_API'))
print(client)
from django.core.management.base import BaseCommand
from app.models import Topic, Subtitle, Card, Quiz
import json


def create_cards_with_quizzes(topic_id, subtitle_id):
    # Set the API key from Django settings
    

    # Retrieve the topic and subtitle from the database
    topic = Topic.objects.get(id=topic_id)
    subtitle = Subtitle.objects.get(id=subtitle_id)
    print(topic, subtitle)

    exists_titles = Card.objects.filter(topic_id=topic_id, subtitle_id=subtitle_id).values_list('title', flat=True)
    full_list_of_titles = list(exists_titles)

    # Formulate the prompt
    prompt = f'''
            Смотри у меня приложение которое будет давать людям изучать краточки с полезными заниями.
            Можешь написать 5 карточек по теме {topic.title} и по подтеме {subtitle.title} это в json где основной контент не 
            занимал более 770 символов с пробелами и это должен быть массив с json с 5 штуками через запятую. 
            Смотри, такие навзания уже есть и ты должен другие карточки {full_list_of_titles}. Надо сделать так чтобы картчоки не повторялись.
            JSON структура такая 
            {{"card": {{"title": "Название картчоки", "content": "Основной текст", "source": "Источник"}},
            "quiz": {{"question": 
            "Сам вопрос квиза", "answers": ["Варианты ответов в массиве"], "correct_answer": "Правильный ответ"}}}}
            Пиши полностью на английском.
            Сам content должен быть побольше от 400 символов до 770.
            Не пиши лишний текст, только json, никаких комментариев от тебя, а то я не смогу принять ответ. 
            Не пиши слово json внчале и вообще ни пиши ни одного лишнего слова, только сам json в ответе и все
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
        response_content = response.choices[0].message.content

        # Remove the triple backticks (```) that enclose the JSON string
        json_string = response_content.strip('`')
        print(json_string)
        # Parse the JSON string
        try:
            cards_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None

        # Extract and process the data
        for card_data in cards_data:
            # Extract card details
            card_title = card_data['card']['title']
            card_content = card_data['card']['content']
            card_source = card_data['card']['source']

            # Create a new Card instance and save it
            card = Card(
                topic=topic,  # Assuming you have the 'topic' variable from earlier in your script
                subtitle=subtitle,  # Assuming you have the 'subtitle' variable from earlier in your script
                title=card_title,
                content=card_content,
                source=card_source
                # You can also set other fields as needed
            )
            card.save()

            # Extract quiz details
            quiz_question = card_data['quiz']['question']
            quiz_answers = card_data['quiz']['answers']
            quiz_correct_answer = card_data['quiz']['correct_answer']

            # Create a new Quiz instance linked to the card and save it
            quiz = Quiz(
                card=card,
                question=quiz_question,
                correct_answer=quiz_correct_answer,
                answers=quiz_answers
            )
            quiz.save()

            print(f"Saved card and quiz for '{card_title}'")

        return response_content
    except Exception as e:
        print(f"Error: {e}")
        return None


class Command(BaseCommand):
    help = 'Описание вашей команды'

    def handle(self, *args, **kwargs):
        for subtitle_id in range(140, 190):  # Перебираем подтемы от 2 до 39
            for _ in range(20):  # Для каждой подтемы повторяем 20 раз
                result = create_cards_with_quizzes(4, subtitle_id)
                self.stdout.write(self.style.SUCCESS(f'Успешно выполнено: {result}'))

