from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import CheckUsernameUniqueView, GetAllTopicsView, CreateUserView, GetUserStatsView, UpdateUserTopicsView, \
    CardListView, QuizListView, MarkCardsAsTestPassed, IncrementReadCards, SaveCard, SavedCards, UsersView, \
    SaveAnswersView, UserBadgeProgressView, CheckUserAchievementsView, UserTopicProgressView

urlpatterns = [
    path('check_unique/<str:username>/', CheckUsernameUniqueView.as_view(), name='check-username-unique'),
    path('topics/', GetAllTopicsView.as_view(), name='get-all-topics'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('user-stats/<int:user_id>/', GetUserStatsView.as_view(), name='user-stats'),
    path('update_topics/<int:user_id>/', UpdateUserTopicsView.as_view(), name='update_user_topics'),
    path('cards/<int:user_id>/', CardListView.as_view(), name='user-card-list'),
    path('quizzes/<int:user_id>/', QuizListView.as_view(), name='quiz-list'),
    path('mark-cards-passed/<int:user_id>/', MarkCardsAsTestPassed.as_view(), name='mark-cards-as-passed'),
    path('update-read-cards-count/<int:user_id>/', IncrementReadCards.as_view(), name='update-read-card'),
    path('save_card/<int:user_id>/', SaveCard.as_view(), name='save-card'),
    path('saved-cards/<int:user_id>/', SavedCards.as_view(), name='saved-cards'),
    path('users_filter/', UsersView.as_view(), name='users'),
    path('update-user-xp/', SaveAnswersView.as_view(), name='update-user-xp'),
    path('user-badge-progress/', UserBadgeProgressView.as_view(), name='user-badge-progress'),
    path('check-achievements/', CheckUserAchievementsView.as_view(), name='check-achievements'),
    path('topics-progress/<int:user_id>/', UserTopicProgressView.as_view(), name='user_topics_progress'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
