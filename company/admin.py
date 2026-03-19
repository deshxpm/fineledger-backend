from django.contrib import admin
from .models import Company, CompanyUser


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'gstin', 'base_currency', 'gst_scheme', 'is_active')
    search_fields = ('name', 'gstin', 'pan')
    list_filter = ('is_active', 'gst_scheme', 'base_currency')


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'is_active')
    list_filter = ('role', 'is_active')
