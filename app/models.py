from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    xp = models.PositiveIntegerField(default=0)
    saved_cards = models.ManyToManyField('Card', blank=True, related_name='users_saved')
    topics = models.ManyToManyField('Topic', blank=True, related_name='users_interested')
    groups = models.ManyToManyField(Group, related_name="customuser_groups")
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_user_permissions")


class Topic(models.Model):
    title = models.CharField(max_length=255)


class Card(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=255)
    users_read = models.ManyToManyField(CustomUser, blank=True, related_name='read_cards')


class Quiz(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='quizzes')
    question = models.TextField()
    correct_answer = models.CharField(max_length=255)
    wrong_answer1 = models.CharField(max_length=255)
    wrong_answer2 = models.CharField(max_length=255)
    wrong_answer3 = models.CharField(max_length=255)


class UserQuizAnswer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_answers')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='user_answers')
    selected_answer = models.CharField(max_length=255)


class Badge(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    users_earned = models.ManyToManyField(CustomUser, blank=True, related_name='earned_badges')


class Leaderboard(models.Model):
    CATEGORY_CHOICES = [
        ('XP', 'Experience Points'),
        ('CARDS', 'Number of Cards Read'),
        ('BADGES', 'Number of Badges Earned'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leaderboard_entries')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    rank = models.PositiveIntegerField()
