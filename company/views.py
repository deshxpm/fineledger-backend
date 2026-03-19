from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Company, CompanyUser
from .serializers import CompanySerializer, CompanyUserSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    CRUD for Companies.
    GET    /api/company/          — list all companies
    POST   /api/company/          — create company
    GET    /api/company/{id}/     — retrieve company
    PUT    /api/company/{id}/     — update company
    PATCH  /api/company/{id}/     — partial update
    DELETE /api/company/{id}/     — delete company
    GET    /api/company/{id}/users/ — list company users
    """
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'short_name', 'gstin']

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        company = self.get_object()
        users = CompanyUser.objects.filter(company=company).select_related('user')
        serializer = CompanyUserSerializer(users, many=True)
        return Response(serializer.data)


class CompanyUserViewSet(viewsets.ModelViewSet):
    queryset = CompanyUser.objects.all().select_related('company', 'user')
    serializer_class = CompanyUserSerializer
    permission_classes = [permissions.IsAuthenticated]
