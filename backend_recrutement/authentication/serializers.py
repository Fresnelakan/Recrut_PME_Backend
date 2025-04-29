from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'last_login', 'email', 'role', 'created_at', 'password','updated_at']

    def create(self, validated_data):
        return User.objects.create_user(
            
            email=validated_data['email'],
            role=validated_data['role'],
            password=validated_data['password']
        )
        
        
        
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token
    
    
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role','created_at','updated_at']