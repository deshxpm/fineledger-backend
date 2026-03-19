"""FinLedger URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'name': 'FinLedger API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'company': '/api/company/',
            'accounts': '/api/accounts/',
            'sales': '/api/sales/',
            'purchase': '/api/purchase/',
            'inventory': '/api/inventory/',
            'dashboard': '/api/dashboard/',
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/auth/', include('finledger_backend.auth_urls')),
    path('api/company/', include('company.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/purchase/', include('purchase.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/dashboard/', include('finledger_backend.dashboard_urls')),
]
