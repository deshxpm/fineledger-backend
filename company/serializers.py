from rest_framework import serializers
from .models import Company, CompanyUser


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class CompanyUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CompanyUser
        fields = ('id', 'company', 'user', 'username', 'email', 'role', 'is_active')
