from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import IncidentSerializer
from .models import Incidents, IncidentStatus


class IncidentsViewSet(ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Incidents.objects.filter(user_id=self.request.user.id).order_by("-started_at", "status")

