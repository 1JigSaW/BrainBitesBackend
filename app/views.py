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

from app.models import CustomUser, Topic, ViewedCard, Card
from app.serializers import TopicSerializer, UserSerializer, BadgeSerializer, UserStatsSerializer, CardSerializer


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

        # Handle the case where user_id is not provided or invalid
        if not user_id:
            return Response({'error': 'User ID must be provided'}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # Assuming the topics relationship and viewed_cards method exist and work correctly
        user_topics = user.topics.all().values_list('id', flat=True)
        limit = 20  # Limit the number of cards to 20

        # Get the IDs of the cards the user has already viewed
        viewed_card_ids = user.viewed_cards.all().values_list('card_id', flat=True)

        # Select cards that the user hasn't viewed yet within their topics
        cards = Card.objects.filter(topic__id__in=user_topics).exclude(id__in=viewed_card_ids)[:limit]

        if not cards:
            return Response({'error': 'No more cards to show'}, status=404)

        # If there are no cards left, it's time for a test
        if not cards.exists():
            # Logic for resetting viewed cards or another mechanism
            # for showing tests or cards again can be implemented here
            return Response({'test_required': True})

        # Create entries for viewed cards
        ViewedCard.objects.bulk_create(
            [ViewedCard(user=user, card=card) for card in cards],
            ignore_conflicts=True
        )

        serializer = CardSerializer(cards, many=True)
        return Response(serializer.data)