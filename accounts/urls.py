from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountGroupViewSet, LedgerViewSet, JournalEntryViewSet

router = DefaultRouter()
router.register(r'groups', AccountGroupViewSet, basename='account-group')
router.register(r'ledgers', LedgerViewSet, basename='ledger')
router.register(r'entries', JournalEntryViewSet, basename='journal-entry')

urlpatterns = [
    path('', include(router.urls)),
]
