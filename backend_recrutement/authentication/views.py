from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework import viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import RegisterSerializer, MyTokenObtainPairSerializer, ProfileSerializer


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ProfileView(APIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
     
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if refresh_token is None:
                return Response({"detail": "Refresh token manquant."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)

        except TokenError as e:
            return Response({"detail": "Token invalide ou déjà blacklisté."}, status=status.HTTP_400_BAD_REQUEST)

