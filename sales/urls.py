from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SalesDocumentViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'documents', SalesDocumentViewSet, basename='sales-document')

urlpatterns = [
    path('', include(router.urls)),
]
