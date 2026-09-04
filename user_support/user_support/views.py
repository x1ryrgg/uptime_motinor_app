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
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)


@extend_schema(
    summary="Register a new user",
    description=(
        "Создает новую учетную запись пользователя.\n\n"
        "Поля `password` и `confirm_password` должны содержать "
        "одно и то же значение. После успешной регистрации "
        "автоматически создаются настройки пользователя по умолчанию."
    ),
    request=UserSerializer,
    responses={
        201: OpenApiResponse(
            response=UserSerializer,
            description="User successfully registered.",
        ),
        400: OpenApiResponse(
            description="Invalid registration data.",
        ),
    },
    examples=[
        OpenApiExample(
            "Registration request",
            summary="Create a new user",
            value={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "12345678",
                "confirm_password": "12345678",
                "first_name": "John",
                "last_name": "Doe",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Registration response",
            summary="Successfully created user",
            value={
                "id": 1,
                "username": "testuser",
                "email": "testuser@example.com",
                "first_name": "John",
                "last_name": "Doe",
            },
            response_only=True,
            status_codes=["201"],
        ),
        OpenApiExample(
            "Passwords do not match",
            summary="Password confirmation error",
            value={
                "confirm_password": [
                    "Passwords do not match."
                ]
            },
            response_only=True,
            status_codes=["400"],
        ),
    ],
)
class RegisterUserView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


@extend_schema(
    summary="Получить или обновить профиль пользователя.",
    description=(
        "Возвращает профиль текущего аутентифицированного пользователя.\n\n"
        "Конечная точка также позволяет частично обновлять профиль пользователя "
        "и настройки с помощью метода `PATCH`.\n\n"
        "Поля `id` и `username` доступны только для чтения."
    ),
    responses={
        200: OpenApiResponse(
            response=PersonalUserSerializer,
            description="Current user's profile.",
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided "
            "or are invalid.",
        ),
    },
    examples=[
        OpenApiExample(
            "Profile response",
            summary="Current user profile",
            value={
                "id": 1,
                "username": "testuser",
                "email": "testuser@example.com",
                "phone_number": "+37060000000",
                "telegram_chat_id": "123456789",
                "first_name": "John",
                "last_name": "Doe",
                "settings": {
                    "id": 1,
                    "email_notification_enabled": True,
                    "telegram_notification_enabled": True,
                    "sms_notification_enabled": False
                },
            },
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Update profile",
            summary="Update user profile",
            value={
                "email": "new_email@example.com",
                "first_name": "John",
                "last_name": "Smith",
                "settings": {
                    "email_notification_enabled": False,
                    "telegram_notification_enabled": False,
                    "sms_notification_enabled": True
                },
            },
            request_only=True,
            status_codes=["200"],
        )
    ],
)
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


@extend_schema(
    summary="Список пользователей",
    description=(
        "Returns a list of all users.\n\n"
        "This endpoint is available only to authenticated users "
        "with administrator privileges."
    ),
    responses={
        200: OpenApiResponse(
            response=UserListSerializer(many=True),
            description="List of users.",
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided "
            "or are invalid.",
        ),
        403: OpenApiResponse(
            description="The authenticated user does not have "
            "administrator privileges.",
        ),
    },
    examples=[
        OpenApiExample(
            "Users list",
            summary="Example users response",
            value=[
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "phone_number": "+37060000000",
                    "telegram_chat_id": "123456789",
                    "is_active": True,
                    "is_superuser": True,
                    "settings": {},
                },
                {
                    "id": 2,
                    "username": "testuser",
                    "email": "testuser@example.com",
                    "phone_number": "+37061111111",
                    "telegram_chat_id": "987654321",
                    "is_active": True,
                    "is_superuser": False,
                    "settings": {},
                },
            ],
            response_only=True,
            status_codes=["200"],
        ),
    ],
)
class UserListView(ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.select_related("settings").order_by("is_active")


# https://github.com/login/oauth/authorize?client_id=CLIENT_ID&scope=user:email
@extend_schema(
    summary="Login with GitHub",
    description=(
        "Authenticates a user using a temporary authorization code "
        "obtained from GitHub OAuth.\n\n"
        "The endpoint exchanges the provided GitHub authorization code "
        "for a GitHub access token, retrieves the GitHub user profile, "
        "creates the local user account if it does not exist, and "
        "returns SimpleJWT access and refresh tokens.\n\n"
        "If the GitHub account does not expose a public email address, "
        "the endpoint attempts to retrieve the user's primary email "
        "from the GitHub API."
    ),
    request=LoginCodeSerializer,
    responses={
        200: OpenApiResponse(
            description="Successfully authenticated with GitHub.",
        ),
        400: OpenApiResponse(
            description=(
                "Invalid GitHub authorization code, GitHub API error, "
                "or the local account is deactivated."
            ),
        ),
    },
    examples=[
        OpenApiExample(
            "GitHub login request",
            summary="Authorization code",
            description=(
                "Temporary authorization code received from GitHub "
                "OAuth authorization flow."
            ),
            value={
                "code": "a1b2c3d4e5f6"
            },
            request_only=True,
        ),
        OpenApiExample(
            "Successful login",
            summary="JWT tokens returned",
            value={
                "refresh": (
                    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                ),
                "access": (
                    "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                ),
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                },
            },
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Invalid GitHub code",
            summary="Invalid authorization code",
            value={
                "error": "Невалидный код или ошибка на стороне GitHub."
            },
            response_only=True,
            status_codes=["400"],
        ),
        OpenApiExample(
            "Deactivated account",
            summary="Account is deactivated",
            value={
                "detail": "Аккаунт деактивирован."
            },
            response_only=True,
            status_codes=["400"],
        ),
    ],
)
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