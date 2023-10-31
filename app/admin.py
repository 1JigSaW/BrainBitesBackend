from django.contrib import admin
from .models import CustomUser, Topic, Card, Quiz, Badge, Leaderboard


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'xp', 'email', 'date_joined']
    search_fields = ['username', 'email']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'source']
    search_fields = ['title', 'content', 'source']
    list_filter = ['topic']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['card', 'question', 'correct_answer']
    search_fields = ['question', 'correct_answer']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'rank']
    search_fields = ['user__username', 'category']
    list_filter = ['category']
