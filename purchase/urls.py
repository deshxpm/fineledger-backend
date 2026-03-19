from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, PurchaseOrderViewSet, PurchaseInvoiceViewSet, PurchaseReturnViewSet

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'invoices', PurchaseInvoiceViewSet, basename='purchase-invoice')
router.register(r'returns', PurchaseReturnViewSet, basename='purchase-return')

urlpatterns = [
    path('', include(router.urls)),
]
