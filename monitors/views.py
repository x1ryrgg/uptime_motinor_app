from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import CheckResultSerializer, MonitorSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Monitor
from rest_framework.viewsets import ModelViewSet


class MonitorViewSet(ModelViewSet):
    """ CRUD для работы с мониторингом пользователя """

    serializer_class = MonitorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Monitor.objects.select_related('user').filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """
        Дополнительный эндпоинт для истории проверок конкретного монитора:
        GET /api/v1/monitors/{id}/history/
        """
        monitor = self.get_object()
        results  = monitor.objects.select_related('user').all()[:100]
        serializer = CheckResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)