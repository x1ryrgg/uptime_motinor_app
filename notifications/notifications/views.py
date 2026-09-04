from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import NotificationSerializer
from .filters import NotificationFilter
from .models import Notifications, NotificationType, NotificationReceiver
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)


@extend_schema_view(
    list=extend_schema(
        summary="List user notifications",
        description=(
            "Returns all notifications belonging to the currently "
            "authenticated user.\n\n"
            "Notifications can be filtered using the available "
            "notification filter parameters."
        ),
        responses={
            200: OpenApiResponse(
                response=NotificationSerializer(many=True),
                description="List of user notifications.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
        },
        examples=[
            OpenApiExample(
                "Notifications list",
                summary="Example notifications",
                value=[
                    {
                        "id": 1,
                        "user_id": 42,
                        "receiver_type": "email",
                        "type": "incident",
                        "title": "Monitor is down",
                        "message": "The monitor example.com is unavailable.",
                        "is_sent": True,
                        "created_at": "2026-09-04T12:30:00Z",
                    },
                    {
                        "id": 2,
                        "user_id": 42,
                        "receiver_type": "telegram",
                        "type": "recovery",
                        "title": "Monitor recovered",
                        "message": "The monitor example.com is available again.",
                        "is_sent": True,
                        "created_at": "2026-09-04T12:35:00Z",
                    },
                ],
                response_only=True,
                status_codes=["200"],
            ),
        ],
    ),
    create=extend_schema(
        summary="Create a notification",
        description=(
            "Creates a new notification for the currently authenticated "
            "user.\n\n"
            "The `user_id` is assigned automatically from the authenticated "
            "user and cannot be changed through the API."
        ),
        responses={
            201: OpenApiResponse(
                response=NotificationSerializer,
                description="Notification successfully created.",
            ),
            400: OpenApiResponse(
                description="Invalid notification data.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
        },
    ),
    retrieve=extend_schema(
        summary="Get notification",
        description=(
            "Returns a specific notification belonging to the "
            "currently authenticated user."
        ),
        responses={
            200: OpenApiResponse(
                response=NotificationSerializer,
                description="Notification details.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Notification was not found.",
            ),
        },
    ),
    update=extend_schema(
        summary="Update notification",
        description=(
            "Updates a notification belonging to the currently "
            "authenticated user."
        ),
        responses={
            200: OpenApiResponse(
                response=NotificationSerializer,
                description="Notification successfully updated.",
            ),
            400: OpenApiResponse(
                description="Invalid notification data.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Notification was not found.",
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update notification",
        description=(
            "Partially updates a notification belonging to the "
            "currently authenticated user."
        ),
        responses={
            200: OpenApiResponse(
                response=NotificationSerializer,
                description="Notification successfully updated.",
            ),
            400: OpenApiResponse(
                description="Invalid notification data.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Notification was not found.",
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete notification",
        description=(
            "Deletes a notification belonging to the currently "
            "authenticated user."
        ),
        responses={
            204: OpenApiResponse(
                description="Notification successfully deleted.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Notification was not found.",
            ),
        },
    ),
)
class NotificationsViewSet(ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationFilter

    def get_queryset(self):
        return Notifications.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

