import csv

from django.contrib import admin
from django.http import HttpResponse
from unfold.admin import ModelAdmin

from .models import WaitlistEntry


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(ModelAdmin):
    list_display = ("email", "created_at", "ip_address")
    search_fields = ("email",)
    list_filter = ("created_at",)
    readonly_fields = ("email", "created_at", "ip_address", "user_agent")
    actions = ("export_csv",)

    def has_add_permission(self, request):
        return False

    @admin.action(description="Export selected to CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=waitlist.csv"
        writer = csv.writer(response)
        writer.writerow(["email", "created_at", "ip_address"])
        for entry in queryset:
            writer.writerow([entry.email, entry.created_at.isoformat(), entry.ip_address or ""])
        return response
