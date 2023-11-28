import random
import string

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Subquery, Count, Window, F
from django.db.models.functions import DenseRank
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import CustomUser, Topic, ViewedCard, Card, Quiz, UserBadgeProgress, Badge, EarnedBadge, Subtitle
from app.serializers import TopicSerializer, UserSerializer, BadgeSerializer, UserStatsSerializer, CardSerializer, \
    QuizSerializer, EarnedBadgeSerializer


class CheckUsernameUniqueView(APIView):
    def get(self, request, username, *args, **kwargs):
        if not username:
            return Response({'isUnique': True}, status=status.HTTP_200_OK)

        is_unique = not CustomUser.objects.filter(username=username).exists()  # используйте CustomUser вместо User

        return Response({'isUnique': is_unique}, status=status.HTTP_200_OK)


class GetAllTopicsView(APIView):
    def get(self, request, *args, **kwargs):
        topics = Topic.objects.all()
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


def generate_random_username(length=8):
    """Generate a random username"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class CreateUserView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        topic_ids = request.data.get('topic_ids', [])
        cards_count = int(request.data.get('cards_count', 10))

        if not username:
            return Response(
                {"error": "Username is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if CustomUser.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that the topic IDs are valid
        topics = Topic.objects.filter(id__in=topic_ids)
        if len(topics) != len(topic_ids):
            return Response(
                {"error": "One or more topics do not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        print(1)
        try:
            # Create a new user with the provided username, topics, and cards count
            with transaction.atomic():
                print(2);
                user = CustomUser.objects.create(
                    username=username,
                    everyday_cards=cards_count
                )
                print(user)
                user.topics.set(topics)
                print(2)
                user.save()

                # Serialize the user data
                user_serializer = UserSerializer(user)
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            print(e)
            return Response(
                {"error": "Failed to create user due to an integrity error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetUserStatsView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            saved_cards_count = user.saved_cards.count()
            read_cards_count = user.read_cards  # Count of read cards
            earned_badges = user.earned_badges.all()
            earned_badges_count = earned_badges.count()
            topics = user.topics.all()

            earned_badges = user.earned_badges.all()
            earned_badges_serialized = EarnedBadgeSerializer(earned_badges, many=True).data

            user_data = {
                'username': user.username,
                'xp': user.xp,
                'saved_cards_count': saved_cards_count,
                'read_cards_count': read_cards_count,
                'earned_badges_count': earned_badges_count,
                # 'earned_badges': earned_badges_serialized,
                'topics': TopicSerializer(topics, many=True).data
            }

            serializer = UserStatsSerializer(user_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class UpdateUserTopicsView(APIView):
    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        topic_ids = request.data.get('topic_ids', [])

        if not user_id:
            return Response(
                {"error": "User ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        topics = Topic.objects.filter(id__in=topic_ids)
        if len(topics) != len(topic_ids):
            return Response(
                {"error": "One or more topics do not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user.topics.set(topics)
                user.save()

                # Serialize the updated user data
                user_serializer = UserSerializer(user)
                return Response(user_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to update user topics due to an unexpected error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CardListView(APIView):

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        user_topics = user.topics.all().values_list('id', flat=True)

        limit = request.query_params.get('limit', 20)
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit value'}, status=400)

        viewed_card_ids = user.viewed_cards.all().values_list('card_id', flat=True)

        cards = Card.objects.filter(topic__id__in=user_topics).exclude(id__in=viewed_card_ids)[:limit]

        ViewedCard.objects.bulk_create(
            [ViewedCard(user=user, card=card) for card in cards],
            ignore_conflicts=True
        )

        serializer = CardSerializer(cards, many=True)
        return Response(serializer.data)


class CardsForSubtitleView(APIView):
    def get(self, request, subtitle_id, user_id, num_cards):
        try:
            subtitle = Subtitle.objects.get(id=subtitle_id)
            user = CustomUser.objects.get(id=user_id)
            viewed_cards = ViewedCard.objects.filter(user=user).values_list('card', flat=True)

            cards = Card.objects.filter(subtitle=subtitle).exclude(id__in=viewed_cards)[:num_cards]
            serializer = CardSerializer(cards, many=True)

            return Response(serializer.data)
        except Subtitle.DoesNotExist:
            return Response({"error": "Subtitle not found"}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class QuizByCardsView(APIView):
    def get(self, request, *args, **kwargs):
        card_ids = self.kwargs.get('card_ids').split(',')
        try:
            quizzes = Quiz.objects.filter(card__id__in=card_ids).distinct()
            serializer = QuizSerializer(quizzes, many=True)
            return Response(serializer.data)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)


class QuizListView(APIView):

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=400)

        viewed_cards = ViewedCard.objects.filter(user_id=user_id, test_passed=False)

        quizzes = Quiz.objects.filter(card__in=[view.card for view in viewed_cards])
        serializer = QuizSerializer(quizzes, many=True)

        return Response(serializer.data)


class MarkCardsAsTestPassed(APIView):

    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=400)

        updated_cards_count = ViewedCard.objects.filter(
            user_id=user_id,
            test_passed=False
        ).update(test_passed=True)

        if updated_cards_count > 0:
            return Response({'message': f'{updated_cards_count} cards marked as test passed.'}, status=200)
        else:
            return Response({'message': 'No cards needed to be updated. All cards are already marked as test passed.'},
                            status=200)


class IncrementReadCards(APIView):

    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        cards_count = request.data.get('read_cards')
        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        if cards_count is None:
            return Response({'error': 'The number of cards to add must be provided'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert cards_count to an integer, and raise an error if it's not valid
            cards_count = int(cards_count)
            if cards_count <= 0:
                raise ValueError("The cards count must be a positive integer.")
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

        try:
            user = CustomUser.objects.get(id=user_id)
            user.read_cards = cards_count
            user.save()

            return Response(
                {'message': f'User read_cards count updated by {cards_count}. New total: {user.read_cards}'},
                status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaveCard(APIView):

    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        card_id = request.data.get('card_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not card_id:
            return Response({'error': 'Card ID must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
            card = Card.objects.get(id=card_id)
            # Check if the card is already saved, if so, remove it
            if card in user.saved_cards.all():
                user.saved_cards.remove(card)
                action = 'removed from'
            else:
                # If the card is not already saved, save it
                user.saved_cards.add(card)
                action = 'saved to'
            user.save()
            return Response(
                {'message': f'Card {card_id} {action} user {user_id}.'},
                status=status.HTTP_200_OK
            )
        except CustomUser.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Card.DoesNotExist:
            return Response({'error': 'Card does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavedCards(APIView):

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
            # Get all saved cards for the user
            saved_cards = user.saved_cards.all()
            # Serialize the card data
            serializer = CardSerializer(saved_cards, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsersView(APIView):

    def get(self, request, *args, **kwargs):
        sort_by = request.query_params.get('sort_by')
        return_all = request.query_params.get('return_all', 'False') == 'True'
        user_id = request.query_params.get('user_id', None)

        try:
            if user_id is not None:
                user_id = int(user_id)

            # Аннотация для подсчета badges_count
            users_query = CustomUser.objects.annotate(badges_count=Count('earned_badges'))

            if return_all:
                # Определение поля для сортировки при return_all=True
                if sort_by in ['xp', 'read_cards', 'badges']:
                    order_by_field = '-badges_count' if sort_by == 'badges' else f'-{sort_by}'
                    users_query = users_query.order_by(order_by_field)

                users_data = UserSerializer(users_query, many=True).data
            else:
                if sort_by not in ['xp', 'read_cards', 'badges']:
                    return Response({'error': 'Invalid sort parameter'}, status=status.HTTP_400_BAD_REQUEST)

                # Определение поля для сортировки
                order_by_field = '-badges_count' if sort_by == 'badges' else f'-{sort_by}'
                users = users_query.order_by(order_by_field)
                top_users = list(users[:3])

                # Определение ранга текущего пользователя
                current_user_rank = None
                if user_id is not None:
                    current_user = users_query.filter(id=user_id).first()
                    if current_user:
                        if sort_by == 'badges':
                            user_value = current_user.badges_count
                            field_for_rank = 'badges_count'
                        else:
                            user_value = getattr(current_user, sort_by)
                            field_for_rank = sort_by

                        current_user_rank = CustomUser.objects.annotate(badges_count=Count('earned_badges')).filter(
                            **{f'{field_for_rank}__gte': user_value}).count()

                        if not any(user.id == user_id for user in top_users):
                            top_users.append(current_user)

                users_data = [
                    {**UserSerializer(user).data, 'user_rank': i + 1}
                    for i, user in enumerate(top_users)
                ]

                # Добавление ранга текущего пользователя
                if current_user_rank is not None:
                    for user_data in users_data:
                        if user_data['id'] == user_id:
                            user_data['user_rank'] = current_user_rank
                            break

            return Response(users_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaveAnswersView(APIView):

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        correct_answers_count = request.data.get('correct_answers_count', 0)

        try:
            if user_id is None or correct_answers_count is None:
                return Response({'error': 'User ID and Correct Answers Count are required.'},
                                status=status.HTTP_400_BAD_REQUEST)

            user = CustomUser.objects.filter(id=user_id).first()
            if not user:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Assuming each correct answer gives 10 XP, for example
            xp_to_add = correct_answers_count * 10

            # Update user XP
            CustomUser.objects.filter(id=user_id).update(xp=F('xp') + xp_to_add)

            # Refresh the user instance to get the updated value
            user.refresh_from_db()

            return Response({'message': 'XP updated successfully.', 'new_xp': user.xp}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserBadgeProgressView(APIView):

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        top_three = request.query_params.get('top_three', 'false').lower() == 'true'

        try:
            if user_id is None:
                return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(CustomUser, id=user_id)

            all_badges = Badge.objects.all()
            user_progress = UserBadgeProgress.objects.filter(user=user)

            earned_badges_ids = EarnedBadge.objects.filter(user=user).values_list('badge', flat=True)

            progress_dict = {progress.badge.id: progress for progress in user_progress}

            badges_list = []
            for badge in all_badges:
                progress_number = progress_dict[badge.id].progress_number if badge.id in progress_dict else 0
                badge_data = {
                    'id': badge.id,
                    'name': badge.name,
                    'description': badge.description,
                    'image': badge.image.url if badge.image else None,
                    'criteria': badge.criteria,
                    'result': badge.result,
                    'progress_number': progress_number,
                    'progress': progress_dict[badge.id].progress if badge.id in progress_dict else {},
                    'is_earned': badge.id in earned_badges_ids
                }
                badges_list.append(badge_data)

            # Объединяем и сортируем список
            badges_list.sort(
                key=lambda x: (
                    x['is_earned'],
                    -abs(x['result'] - x['progress_number']) if x['progress_number'] != 0 else float('inf'))
            )

            # Возвращаем только топ-3, если требуется
            if top_three:
                badges_list = badges_list[:3]

            return Response({'badge_progress': badges_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckUserAchievementsView(APIView):

    def get(self, request, *args, **kwargs):
        print(11111111111111111111111111111111111111)
        user_id = request.query_params.get('user_id')
        if user_id is None:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, id=user_id)

        earned_badges = []
        all_badges = Badge.objects.all()
        user_progress = UserBadgeProgress.objects.filter(user=user)
        for badge in all_badges:
            print(badge.criteria)

            # Проверяем, был ли значок уже заработан
            already_earned = EarnedBadge.objects.filter(user=user, badge=badge).exists()

            # Если значок уже заработан, пропускаем его
            if already_earned:
                print('already_earned', already_earned)
                continue

            # Используйте метод get() со значением по умолчанию, например, False
            if badge.criteria.get('read_cards', False):
                user_progress = UserBadgeProgress.objects.get_or_create(user=user, badge=badge)
                viewed_cards = ViewedCard.objects.filter(user=user, test_passed=True)
                user_progress[0].progress_number = viewed_cards.count()
                user_progress[0].save()
                if user_progress[0].progress_number >= badge.criteria['read_cards']:
                    already_earned = EarnedBadge.objects.filter(user=user, badge=badge).exists()
                    if not already_earned:
                        earned_badge, badge_created = EarnedBadge.objects.get_or_create(user=user, badge=badge)
                        if badge_created:
                            earned_badges.append({
                                'name': badge.name,
                                # Другие поля
                            })
            elif 'read_specific_topic' in badge.criteria:
                user_progress = UserBadgeProgress.objects.get_or_create(user=user, badge=badge)
                topic_id = badge.criteria['read_specific_topic']['topic_id']
                viewed_cards = ViewedCard.objects.filter(user=user, card__topic_id=topic_id, test_passed=True)
                user_progress[0].progress_number = viewed_cards.count()
                user_progress[0].save()

                if user_progress[0].progress_number >= badge.criteria['read_specific_topic']['count']:
                    already_earned = EarnedBadge.objects.filter(user=user, badge=badge).exists()
                    if not already_earned:
                        earned_badge, badge_created = EarnedBadge.objects.get_or_create(user=user, badge=badge)
                        if badge_created:
                            earned_badges.append({
                                'name': badge.name,
                                # Другие поля
                            })

            elif 'quiz_specific_topic' in badge.criteria:
                user_progress = UserBadgeProgress.objects.get_or_create(user=user, badge=badge)

                passed_viewed_cards = ViewedCard.objects.filter(
                    user=user,
                    test_passed=True,
                    card__topic_id=badge.criteria["quiz_specific_topic"]["topic_id"]
                )

                passed_quizzes_count = passed_viewed_cards.values('card').distinct().count()
                user_progress[0].progress_number = passed_quizzes_count
                user_progress[0].save()

                if user_progress[0].progress_number >= badge.criteria['quiz_specific_topic']['count']:
                    already_earned = EarnedBadge.objects.filter(user=user, badge=badge).exists()
                    if not already_earned:
                        earned_badge, badge_created = EarnedBadge.objects.get_or_create(user=user, badge=badge)
                        if badge_created:
                            earned_badges.append({
                                'name': badge.name,
                                # Другие поля
                            })
        print('earned_badges', earned_badges)
        return Response({'earned_badges': earned_badges}, status=status.HTTP_200_OK)


class UserTopicProgressView(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user_topics = Topic.objects.filter(users_interested=user)  # Corrected line
        topics_data = []

        for topic in user_topics:
            viewed_cards = ViewedCard.objects.filter(user=user, card__topic=topic)
            total_viewed = viewed_cards.count()
            total_cards = Card.objects.filter(topic=topic).count()
            progress = total_viewed / total_cards if total_cards > 0 else 0

            topics_data.append({
                'topic_id': topic.id,
                'topic_name': topic.title,  # Corrected field name from 'name' to 'title'
                'progress': progress,
                'viewed_cards': total_viewed,
                'total_cards': total_cards
            })

        return JsonResponse({'user_topics': topics_data})


class UserSubtitleProgressView(APIView):
    def get(self, request, topic_id, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            topic = Topic.objects.get(id=topic_id)
        except ObjectDoesNotExist:
            return Response({"error": "User or Topic not found."}, status=status.HTTP_404_NOT_FOUND)

        cards_in_topic = Card.objects.filter(topic=topic)
        print('cards_in_topic', cards_in_topic)
        subtitles = Subtitle.objects.filter(id__in=cards_in_topic.values('subtitle_id')).distinct()
        subtitle_data = []

        for subtitle in subtitles:
            cards_in_subtitle = cards_in_topic.filter(subtitle=subtitle)
            viewed_cards = ViewedCard.objects.filter(user=user, card__in=cards_in_subtitle)
            total_viewed = viewed_cards.count()
            total_cards = cards_in_subtitle.count()
            progress = total_viewed / total_cards if total_cards > 0 else 0

            subtitle_data.append({
                'subtitle_id': subtitle.id,
                'subtitle_name': subtitle.title,  # Assuming Subtitle model has a name field
                'progress': progress,
                'viewed_cards': total_viewed,
                'total_cards': total_cards
            })
        print(subtitle_data)
        return JsonResponse({'subtitles_progress': subtitle_data})
