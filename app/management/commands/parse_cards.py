import os
import threading
import time
import json
from openai import OpenAI
from django.core.management.base import BaseCommand
from app.models import Topic, Subtitle, Card, Quiz
from threading import Semaphore

# Настройка клиента OpenAI
print(os.environ.get('OPENAI_API'))
client = OpenAI(api_key=os.environ.get('OPENAI_API'))
print(client)

# Инициализация семафора
max_parallel_requests = 30
semaphore = Semaphore(max_parallel_requests)


# Функция для создания карточек с викторинами
def create_cards_with_quizzes(topic_id, subtitle_id):
    semaphore.acquire()  # Захват слота в семафоре
    try:
        topic = Topic.objects.get(id=topic_id)
        subtitle = Subtitle.objects.get(id=subtitle_id)
        print(topic, subtitle)

        exists_titles = Card.objects.filter(topic_id=topic_id, subtitle_id=subtitle_id).values_list('title', flat=True)
        full_list_of_titles = list(exists_titles)

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

        # Расчет задержки на основе ограничения токенов
        token_usage_per_request = 500
        requests_per_minute = 10000 // token_usage_per_request
        time_delay = 60 / requests_per_minute

        # Запрос к API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        print(response)
        response_content = response.choices[0].message.content
        json_string = response_content.strip('`')
        print(json_string)

        cards_data = json.loads(json_string)

        for card_data in cards_data:
            card_title = card_data['card']['title']
            card_content = card_data['card']['content']
            card_source = card_data['card']['source']

            card = Card(topic=topic, subtitle=subtitle, title=card_title, content=card_content, source=card_source)
            card.save()

            quiz_question = card_data['quiz']['question']
            quiz_answers = card_data['quiz']['answers']
            quiz_correct_answer = card_data['quiz']['correct_answer']

            quiz = Quiz(card=card, question=quiz_question, correct_answer=quiz_correct_answer, answers=quiz_answers)
            quiz.save()

            print(f"Saved card and quiz for '{card_title}'")

        time.sleep(time_delay)  # Задержка перед следующим запросом

        return response_content

    except Exception as e:
        print(f"Error: {e}")
        if 'rate_limit_exceeded' in str(e):
            wait_time = extract_wait_time(str(e))
            print(f"Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
            return create_cards_with_quizzes(topic_id, subtitle_id)
        return None
    finally:
        semaphore.release()  # Освобождение слота в семафоре

    # Функция для извлечения времени ожидания из сообщения об ошибке


def extract_wait_time(error_message):
    try:
        start = error_message.find('in ') + 3
        end = error_message.find('s', start)
        wait_time = float(error_message[start:end])
        return wait_time
    except ValueError:
        return 60  # Стандартное время ожидания, если не удается извлечь точное время

    # Командный класс


class Command(BaseCommand):
    help = 'Описание вашей команды'

    @staticmethod
    def thread_function(subtitle_id):
        for _ in range(20):  # Для каждой подтемы повторяем 20 раз
            result = create_cards_with_quizzes(14, subtitle_id)
            print(f'Успешно выполнено: {result}')

    def handle(self, *args, **kwargs):
        threads = []
        for subtitle_id in range(588, 637):  # Перебираем подтемы
            t = threading.Thread(target=Command.thread_function, args=(subtitle_id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()


# Запуск скрипта
if __name__ == "__main__":
    Command().handle()
