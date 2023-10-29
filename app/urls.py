from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import CheckUsernameUniqueView, GetAllTopicsView, CreateUserView

urlpatterns = [
    path('check_unique/<str:username>/', CheckUsernameUniqueView.as_view(), name='check-username-unique'),
    path('topics/', GetAllTopicsView.as_view(), name='get-all-topics'),
    path('create-user/', CreateUserView.as_view(), name='create_user'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()