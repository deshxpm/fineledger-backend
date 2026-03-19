from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, CompanyUserViewSet

router = DefaultRouter()
router.register(r'', CompanyViewSet, basename='company')
router.register(r'users', CompanyUserViewSet, basename='company-user')

urlpatterns = [
    path('', include(router.urls)),
]
