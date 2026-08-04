from django.shortcuts import render

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView

from .models import User
from .permissions import IsSuperUser
from .serializers import UserSerializer, PersonalUserSerializer


class RegisterUserView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ProfileView(RetrieveUpdateDestroyAPIView):
    serializer_class = PersonalUserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete"]

    def get_object(self):
        return User.objects.select_related("settings").get(id=self.request.user.id)
