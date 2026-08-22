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


logger = get_logger(__name__)

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
            {"detail": f"Ручная проверка монитора #{monitor.pk} запущена."},
            status=status.HTTP_202_ACCEPTED,
        )
