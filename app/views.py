import random
import string

from django.db import transaction, IntegrityError
from django.db.models import Subquery
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import CustomUser, Topic, ViewedCard, Card, Quiz
from app.serializers import TopicSerializer, UserSerializer, BadgeSerializer, UserStatsSerializer, CardSerializer, \
    QuizSerializer


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
        print(username, topic_ids)
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

        try:
            # Create a new user with the provided username and topics
            with transaction.atomic():
                user = CustomUser.objects.create(username=username)
                user.topics.set(topics)
                user.save()

                # Serialize the user data
                user_serializer = UserSerializer(user)
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            return Response(
                {"error": "Failed to create user due to an integrity error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetUserStatsView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        print('user_id', user_id)
        try:
            user = CustomUser.objects.get(id=user_id)
            saved_cards_count = user.saved_cards.count()
            read_cards_count = user.read_cards  # Count of read cards
            earned_badges = user.earned_badges.all()
            earned_badges_count = earned_badges.count()
            topics = user.topics.all()

            user_data = {
                'username': user.username,
                'xp': user.xp,
                'saved_cards_count': saved_cards_count,
                'read_cards_count': read_cards_count,  # Include read cards count here
                'earned_badges_count': earned_badges_count,
                'earned_badges': BadgeSerializer(earned_badges, many=True).data if earned_badges else [],
                'topics': TopicSerializer(topics, many=True).data
            }

            # Serialize the data
            serializer = UserStatsSerializer(user_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class UpdateUserTopicsView(APIView):
    def put(self, request, *args, **kwargs):
        print('request');
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
        print('serializer', cards)
        return Response(serializer.data)


class QuizListView(APIView):

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=400)

        viewed_cards = ViewedCard.objects.filter(user_id=user_id, test_passed=False)

        quizzes = Quiz.objects.filter(card__in=[view.card for view in viewed_cards])
        serializer = QuizSerializer(quizzes, many=True)
        print('quizzes', quizzes)

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
        print('request.data', request.data);
        user_id = kwargs.get('user_id')
        cards_count = request.data.get('read_cards')
        print('read_cards', cards_count)
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
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
            user.read_cards += cards_count
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
        print('request.data', request.data)
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
        print(2)
        user_id = kwargs.get('user_id')

        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print(1)
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