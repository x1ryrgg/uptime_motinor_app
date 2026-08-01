from django.db.models import Prefetch
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import IncidentSerializer
from .models import Incidents, IncidentStatus


class IncidentsViewSet(ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Incidents.objects.filter(monitor__user_id=self.request.user.id)

