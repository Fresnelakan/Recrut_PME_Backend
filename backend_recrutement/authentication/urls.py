from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import LogoutView, MyTokenObtainPairView, RegisterView, ProfileView
import authentication.views as views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/',views.MyTokenObtainPairView.as_view() , name='login'),
    path('refresh/',TokenRefreshView.as_view(),name='refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'), 


]
