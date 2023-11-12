from django.contrib import admin
from django import forms

from .models import CustomUser, Topic, Card, Quiz, Badge, Leaderboard, EarnedBadge


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


class QuizAdminForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = '__all__'  # Используйте все поля модели Quiz

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        # Получаем id карт, для которых уже есть quiz
        existing_quiz_cards = Quiz.objects.values_list('card', flat=True)
        # Исключаем их из queryset поля card
        self.fields['card'].queryset = Card.objects.exclude(id__in=existing_quiz_cards)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm
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


@admin.register(EarnedBadge)
class EarnedBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'date_earned']
    search_fields = ['user__username', 'badge__name']
    list_filter = ['badge', 'date_earned']

    def get_queryset(self, request):
        # Customize the queryset if needed, for example, you can prefetch related objects
        return super().get_queryset(request).select_related('user', 'badge')