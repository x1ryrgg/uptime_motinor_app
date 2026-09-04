from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import IncidentSerializer
from .models import Incidents, IncidentStatus
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)


@extend_schema_view(
    list=extend_schema(
        summary="List user incidents",
        description=(
            "Returns all incidents belonging to the currently "
            "authenticated user.\n\n"
            "Incidents are ordered by start time in descending order. "
            "For incidents with the same start time, they are ordered "
            "by status."
        ),
        responses={
            200: OpenApiResponse(
                response=IncidentSerializer(many=True),
                description="List of user incidents.",
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
                "Incidents list",
                summary="Example incidents",
                value=[
                    {
                        "id": 15,
                        "monitor_id": 42,
                        "status": "resolved",
                        "started_at": "2026-09-04T12:00:00Z",
                        "resolved_at": "2026-09-04T12:03:27Z",
                        "duration_seconds": 207,
                        "cause": "HTTP 500 response",
                    },
                    {
                        "id": 14,
                        "monitor_id": 42,
                        "status": "ongoing",
                        "started_at": "2026-09-04T11:30:00Z",
                        "resolved_at": None,
                        "duration_seconds": None,
                        "cause": "Connection timeout",
                    },
                ],
                response_only=True,
                status_codes=["200"],
            ),
        ],
    ),
    create=extend_schema(
        summary="Create an incident",
        description=(
            "Creates a new incident.\n\n"
            "The incident is associated with a monitor using "
            "`monitor_id`."
        ),
        responses={
            201: OpenApiResponse(
                response=IncidentSerializer,
                description="Incident successfully created.",
            ),
            400: OpenApiResponse(
                description="Invalid incident data.",
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
        summary="Get incident",
        description=(
            "Returns a specific incident belonging to the "
            "currently authenticated user."
        ),
        responses={
            200: OpenApiResponse(
                response=IncidentSerializer,
                description="Incident details.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Incident was not found.",
            ),
        },
    ),
    update=extend_schema(
        summary="Update incident",
        description=(
            "Updates an incident belonging to the currently "
            "authenticated user."
        ),
        responses={
            200: OpenApiResponse(
                response=IncidentSerializer,
                description="Incident successfully updated.",
            ),
            400: OpenApiResponse(
                description="Invalid incident data.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Incident was not found.",
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update incident",
        description=(
            "Partially updates an incident belonging to the "
            "currently authenticated user."
        ),
        responses={
            200: OpenApiResponse(
                response=IncidentSerializer,
                description="Incident successfully updated.",
            ),
            400: OpenApiResponse(
                description="Invalid incident data.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Incident was not found.",
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete incident",
        description=(
            "Deletes an incident belonging to the currently "
            "authenticated user."
        ),
        responses={
            204: OpenApiResponse(
                description="Incident successfully deleted.",
            ),
            401: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided "
                    "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Incident was not found.",
            ),
        },
    ),
)
class IncidentsViewSet(ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Incidents.objects.filter(user_id=self.request.user.id).order_by("-started_at", "status")

