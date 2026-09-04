from shared_logging.logging import get_logger
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .serializers import CheckResultSerializer, MonitorSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Monitor, CheckResult
from rest_framework.viewsets import ModelViewSet
from django.db.models import Prefetch

from .services import execute_monitor_check
from .tasks import run_single_monitor_task
from .throttling import BurstManualCheckThrottle, DailyManualCheckThrottle
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)


logger = get_logger(__name__)


@extend_schema(
    tags=["Monitors"],
)
class MonitorViewSet(ModelViewSet):
    """CRUD для работы с мониторингом пользователя"""

    serializer_class = MonitorSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        latest_checks = CheckResult.objects.order_by("-checked_at")

        return (
            Monitor.objects.filter(user_id=self.request.user.id)
            .prefetch_related(
                Prefetch(
                    "check_results",
                    queryset=latest_checks,
                    to_attr="prefetched_last_checks",
                )
            )
            .order_by("-id")
        )

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

    @extend_schema(
        summary="Get monitor check history",
        description=(
                "Returns the check history for the specified monitor.\n\n"
                "Only monitors belonging to the currently authenticated "
                "user can be accessed.\n\n"
                "The endpoint returns up to 100 check results."
        ),
        responses={
            200: OpenApiResponse(
                response=CheckResultSerializer(many=True),
                description="Monitor check history.",
            ),
            401: OpenApiResponse(
                description=(
                        "Authentication credentials were not provided "
                        "or are invalid."
                ),
            ),
            404: OpenApiResponse(
                description="Monitor was not found.",
            ),
        },
        examples=[
            OpenApiExample(
                "Check history",
                summary="Example monitor history",
                value=[
                    {
                        "id": 101,
                        "status_code": 200,
                        "response_time_ms": 143,
                        "is_success": True,
                        "checked_at": "2026-09-04T12:30:00Z",
                    },
                    {
                        "id": 100,
                        "status_code": 500,
                        "response_time_ms": 821,
                        "is_success": False,
                        "checked_at": "2026-09-04T12:29:00Z",
                    },
                ],
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        """
        Дополнительный эндпоинт для истории проверок конкретного монитора:
        GET /api/v1/monitors/{id}/history/
        """
        monitor = self.get_object()
        results = monitor.check_results.all()[:100]
        serializer = CheckResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Run monitor check manually",
    description=(
        "Starts a manual check for the specified monitor.\n\n"
        "The check is executed asynchronously by a background task. "
        "The endpoint returns immediately after the task has been "
        "successfully queued.\n\n"
        "A user can only manually check monitors belonging to their "
        "own account.\n\n"
        "The endpoint is protected by burst and daily rate limits."
    ),
    request=None,
    responses={
        202: OpenApiResponse(
            description="Monitor check successfully queued.",
        ),
        401: OpenApiResponse(
            description=(
                "Authentication credentials were not provided "
                "or are invalid."
            ),
        ),
        404: OpenApiResponse(
            description="Monitor was not found.",
        ),
        429: OpenApiResponse(
            description=(
                "Rate limit exceeded. The user has reached either "
                "the burst or daily limit for manual checks."
            ),
        ),
    },
    examples=[
        OpenApiExample(
            "Successful manual check",
            summary="Check queued",
            value={
                "detail": "Success check manually {monitor.name}"
            },
            response_only=True,
            status_codes=["202"],
        ),
    ],
)
class ManualCheckView(APIView):
    """
    Ручная проверка монитора.
    POST api/v1/monitoring/{id}/manual/
    """

    permission_classes = (IsAuthenticated, )
    throttle_classes = (BurstManualCheckThrottle, DailyManualCheckThrottle, )

    def post(self, request, monitor_id: int, *args, **kwargs):
        monitor = get_object_or_404(Monitor, pk=monitor_id, user_id=request.user.id)

        run_single_monitor_task.delay(monitor_id=monitor_id)

        logger.info(
            "Forced start run_single_monitor_task",
            user_id=request.user.id,
            monitor_id=monitor_id
        )
        
        return Response(
            {"detail": f"Success check manually {monitor.name}"},
            status=status.HTTP_202_ACCEPTED,
        )
