from django.http import JsonResponse
from django.views import View
from django.contrib.auth.models import User


class CheckUsernameUniqueView(View):
    def get(self, request, *args, **kwargs):
        username = kwargs.get('username')
        if not username:
            return JsonResponse(
                {'isUnique': True})

        is_unique = not User.objects.filter(username=username).exists()

        return JsonResponse({'isUnique': is_unique})
