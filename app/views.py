import random
import string

from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import CustomUser, Topic
from app.serializers import TopicSerializer, UserSerializer


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
