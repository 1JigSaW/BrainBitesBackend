from rest_framework import serializers
from .models import Topic, CustomUser


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ('id', 'title')


class UserSerializer(serializers.ModelSerializer):
    saved_cards = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'xp', 'saved_cards', 'topics')
