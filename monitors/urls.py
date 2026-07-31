from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonitorViewSet

monitoring_router = DefaultRouter()
monitoring_router.register(r"", MonitorViewSet, basename="monitor")

urlpatterns = [path("monitoring/", include(monitoring_router.urls))]
