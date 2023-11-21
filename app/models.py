from cloudinary.models import CloudinaryField
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    xp = models.PositiveIntegerField(default=0)
    saved_cards = models.ManyToManyField('Card', blank=True, related_name='users_saved')
    read_cards = models.PositiveIntegerField(default=0)
    topics = models.ManyToManyField('Topic', blank=True, related_name='users_interested')
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_user_permissions", blank=True)


class Topic(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.title}"


class Subtitle(models.Model):
    title = models.CharField(max_length=255)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic')


class Card(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='cards')
    subtitle = models.ForeignKey(Subtitle, on_delete=models.CASCADE, related_name='subtitle', null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=255)
    read_count = models.PositiveIntegerField(default=0)  # Tracks how many times the card has been read
    image = CloudinaryField('image')

    def __str__(self):
        return f"{self.title} {self.topic.title}"


class ViewedCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewed_cards')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='viewed_by_users')
    date_viewed = models.DateTimeField(auto_now_add=True)
    test_passed = models.BooleanField(default=False)  # Новое поле для отслеживания прохождения теста

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

