from django.db.models import Prefetch
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import IncidentSerializer
from .models import Incidents, IncidentStatus
from monitors.models import Monitor


class IncidentsViewSet(ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Incidents.objects.filter(monitor__user=self.request.user).select_related(
            "monitor"
        )


# Нужно прописать логику создания Incidents при постоянном падении ошибки при нескольких интерацих относительно interval_seconds
