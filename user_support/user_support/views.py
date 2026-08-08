import requests

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, ListAPIView

from .models import User, UserSettings
from .permissions import IsSuperUser
from .serializers import UserSerializer, PersonalUserSerializer, LoginCodeSerializer, UserListSerializer


class RegisterUserView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ProfileView(RetrieveUpdateAPIView):
    serializer_class = PersonalUserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return User.objects.select_related("settings").get(id=self.request.user.id)


class DeactivateUserView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        user = request.user
        user.is_active = False
        user.save()

        return Response(
            {"detail": "Аккаунт успешно деактивирован."},
            status=status.HTTP_200_OK
        )


class UserListView(ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.select_related("settings").order_by("is_active")

# https://github.com/login/oauth/authorize?client_id=CLIENT_ID&scope=user:email
class GitHubLoginView(APIView):
    serializer_class = LoginCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        # 1. Обмениваем временный code на access_token от GitHub
        token_url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        }
        headers = {"Accept": "application/json"}
        token_response = requests.post(url=token_url, json=payload, headers=headers)
        token_data = token_response.json()

        github_access_token = token_data.get("access_token")
        if not github_access_token:
            return Response(
                {"error": "Невалидный код или ошибка на стороне GitHub."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Получаем данные профиля пользователя от GitHub API
        user_headers = {"Authorization": f"Bearer {github_access_token}"}
        user_response = requests.get("https://api.github.com/user", headers=user_headers)
        user_data = user_response.json()

        github_username = user_data.get("login")
        email = user_data.get("email")

        # Если у пользователя email скрыт в приватных настройках GitHub,
        # запрашиваем список всех его привязанных почт:
        if not email:
            emails_response = requests.get(
                "https://api.github.com/user/emails", headers=user_headers
            )
            if emails_response.status_code == 200:
                emails = emails_response.json()
                primary_email = next(
                    (e["email"] for e in emails if e.get("primary")), None
                )
                email = primary_email or f"{github_username}@github.com"
            else:
                email = f"{github_username}@github.com"

        # 3. Находим пользователя в базе или создаем нового
        user, created = User.objects.get_or_create(
            username=github_username,
            defaults={
                "email": email,
                "first_name": user_data.get("name") or "",
            },
        )

        if created:
            user.set_unusable_password()
            user.save()
            UserSettings.objects.create(user=user)

        # Если пользователь был неактивен, разрешаем вход или проверяем статус
        if not user.is_active:
            return Response(
                {"detail": "Аккаунт деактивирован."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Генерируем SimpleJWT токены
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.pk,
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )