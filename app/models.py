import pytz
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone

from BrainBites import settings


class Topic(models.Model):
    title = models.CharField(max_length=255)
    image = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title}"


class Subtitle(models.Model):
    title = models.CharField(max_length=255)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic')
    is_free = models.BooleanField(default=False)
    image = models.URLField(blank=True, null=True)
    cost = models.PositiveIntegerField(default=200)
    exist = models.BooleanField(default=True)


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True, blank=False, null=False)
    xp = models.PositiveIntegerField(default=0)
    saved_cards = models.ManyToManyField('Card', blank=True, related_name='users_saved')
    read_cards = models.PositiveIntegerField(default=0)
    topics = models.ManyToManyField('Topic', blank=True, related_name='users_interested')
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_user_permissions", blank=True)
    everyday_cards = models.PositiveIntegerField(default=10)
    purchased_subtitles = models.ManyToManyField(Subtitle, through='UserSubtitle', related_name='purchasers')
    avatar_url = models.URLField(max_length=200, blank=True)
    lives = models.PositiveIntegerField(default=5)
    last_life_lost_time = models.DateTimeField(default=timezone.now)


class Card(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='cards')
    subtitle = models.ForeignKey(Subtitle, on_delete=models.CASCADE, related_name='subtitle', null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=255)
    read_count = models.PositiveIntegerField(default=0)  # Tracks how many times the card has been read
    image = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} {self.topic.title}"


class ViewedCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewed_cards')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='viewed_by_users')
    date_viewed = models.DateTimeField(auto_now_add=True)
    test_passed = models.BooleanField(default=False)
    correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'card')


class Quiz(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='quizzes')
    question = models.TextField()
    correct_answer = models.CharField(max_length=255)
    answers = models.JSONField(default=list)  # Store all answers as a JSON list

    def __str__(self):
        return f"{self.card.title} {self.question} "


class UserQuizStatistics(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_stats')
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    incorrect_attempts = models.PositiveIntegerField(default=0)


class Badge(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/', default='path/to/my/default/image.jpg')
    criteria = models.JSONField(default=dict)
    result = models.PositiveIntegerField(default=0)


class EarnedBadge(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='earned_by')
    date_earned = models.DateTimeField(auto_now_add=True)


class UserBadgeProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='badge_progress')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_progress')
    progress_number = models.PositiveIntegerField(default=0)
    progress = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user}'s progress on {self.badge}"


class Leaderboard(models.Model):
    CATEGORY_CHOICES = [
        ('XP', 'Experience Points'),
        ('CARDS', 'Number of Cards Read'),
        ('BADGES', 'Number of Badges Earned'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leaderboard_entries')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    rank = models.PositiveIntegerField()


class UserSubtitle(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_subtitles')
    subtitle = models.ForeignKey(Subtitle, on_delete=models.CASCADE, related_name='purchased_by_users')
    cost_in_xp = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} purchased {self.subtitle.title} for {self.cost_in_xp} XP"


class UserStreak(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='streaks')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    def update_streak(self):
        user_tz = pytz.timezone(self.timezone)
        today = timezone.now().astimezone(user_tz).date()
        streak_broken = False

        if self.last_streak_date:
            if self.last_streak_date == today - timezone.timedelta(days=1):
                self.current_streak += 1
            elif self.last_streak_date < today - timezone.timedelta(days=1):
                self.current_streak = 1
                streak_broken = True
        else:
            self.current_streak = 1

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_streak_date = today
        self.save()

        return streak_broken


class DailyReadCards(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='daily_read_cards')
    date = models.DateField()
    cards_read = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')


class CorrectStreak(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='correct_streaks')
    streak_count = models.PositiveIntegerField(default=0)
    max_streak = models.PositiveIntegerField(default=0)
    last_quiz_fully_correct = models.BooleanField(default=False)

    def update_streak(self, quiz_correct_answers, total_quiz_questions):
        if quiz_correct_answers == total_quiz_questions:
            self.streak_count += quiz_correct_answers
            self.last_quiz_fully_correct = True
        else:
            if not self.last_quiz_fully_correct:
                self.streak_count = quiz_correct_answers if quiz_correct_answers == total_quiz_questions else 0
            self.last_quiz_fully_correct = False

        if self.streak_count > self.max_streak:
            self.max_streak = self.streak_count

        self.save()
