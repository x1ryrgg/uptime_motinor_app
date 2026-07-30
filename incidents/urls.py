from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncidentsViewSet


incidents_router = DefaultRouter()
incidents_router.register(r"", IncidentsViewSet, basename="incidents")

urlpatterns = [
    path("incidents/", include(incidents_router.urls))
]
