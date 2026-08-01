from django.db import models


class WaitlistEntry(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "waitlist entry"
        verbose_name_plural = "waitlist entries"

    def __str__(self):
        return self.email
