from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import CheckUsernameUniqueView, GetAllTopicsView, CreateUserView, GetUserStatsView, UpdateUserTopicsView, \
    GetRandomCardsView

urlpatterns = [
    path('check_unique/<str:username>/', CheckUsernameUniqueView.as_view(), name='check-username-unique'),
    path('topics/', GetAllTopicsView.as_view(), name='get-all-topics'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('user-stats/<int:user_id>/', GetUserStatsView.as_view(), name='user-stats'),
    path('update_topics/<int:user_id>/', UpdateUserTopicsView.as_view(), name='update_user_topics'),
    path('cards/<int:user_id>/', GetRandomCardsView.as_view(), name='get-cards'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()