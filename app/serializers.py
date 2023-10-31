from rest_framework import serializers
from .models import Topic, CustomUser, Card, Subtitle


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ('id', 'title')


class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitle
        fields = ('id', 'title')


class UserSerializer(serializers.ModelSerializer):
    saved_cards = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'xp', 'saved_cards', 'topics')


class BadgeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField()


class UserStatsSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    xp = serializers.IntegerField()
    saved_cards_count = serializers.IntegerField()
    read_cards_count = serializers.IntegerField()  # Add this field
    earned_badges_count = serializers.IntegerField()
    earned_badges = BadgeSerializer(many=True)
    topics = TopicSerializer(many=True)

    def validate_xp(self, value):
        # You can add custom validation for experience points here
        if value < 0:
            raise serializers.ValidationError("XP cannot be negative.")
        return value


class CardSerializer(serializers.ModelSerializer):
    topic = serializers.StringRelatedField()
    subtitle = serializers.StringRelatedField()
    class Meta:
        model = Card
        fields = ['id', 'topic', 'subtitle', 'title', 'content', 'source', 'read_count', 'image']