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


class BadgeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField()


class UserStatsSerializer(serializers.Serializer):
    xp = serializers.IntegerField()
    saved_cards_count = serializers.IntegerField()
    earned_badges_count = serializers.IntegerField()
    earned_badges = BadgeSerializer(many=True)
    username = serializers.CharField();

    def validate_xp(self, value):
        # You can add custom validation for experience points here
        if value < 0:
            raise serializers.ValidationError("XP cannot be negative.")
        return value
