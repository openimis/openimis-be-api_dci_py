"""
DCI API Models

Models for SPDCI subscription and event notification management.
"""
import uuid
from django.db import models
from django.utils.translation import gettext as _
from django_cryptography.fields import encrypt

from core.datetimes import ad_datetime
from core.fields import DateTimeField
from core.models import HistoryBusinessModel


class DCISubscription(HistoryBusinessModel):
    """
    SPDCI Registry Subscription

    Stores subscription information for event notifications following
    SPDCI FR/SR/IBR standards.
    """

    class SubscriptionStatus(models.IntegerChoices):
        INACTIVE = 0, _("inactive")
        ACTIVE = 1, _("active")
        SUSPENDED = 2, _("suspended")

    class EventType(models.TextChoices):
        """SPDCI Event Types"""
        REGISTER = 'REGISTER', _("Register")
        UPDATE = 'UPDATE', _("Update")
        DEREGISTER = 'DEREGISTER', _("Deregister")
        ALL = 'ALL', _("All events")

    # Subscription metadata
    subscription_code = models.CharField(
        db_column="SubscriptionCode",
        max_length=255,
        unique=True,
        null=False,
        help_text="Unique subscription identifier returned to client"
    )

    # Subscriber information
    sender_id = models.CharField(
        db_column="SenderId",
        max_length=255,
        null=False,
        help_text="ID of the subscribing system (from header.sender_id)"
    )

    sender_uri = models.URLField(
        db_column="SenderUri",
        max_length=500,
        blank=True,
        null=True,
        help_text="Callback URL for notifications (from header.sender_uri, optional)"
    )

    # Subscription criteria (SPDCI format)
    event_type = models.CharField(
        db_column="EventType",
        max_length=50,
        choices=EventType.choices,
        default=EventType.ALL,
        null=False
    )

    filter_criteria = models.JSONField(
        db_column="FilterCriteria",
        blank=True,
        null=True,
        help_text="SPDCI query filter (idtype-value, expression, predicate)"
    )

    # Subscription status
    status = models.SmallIntegerField(
        db_column="Status",
        null=False,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )

    # Callback configuration
    callback_headers = encrypt(
        models.TextField(
            db_column="CallbackHeaders",
            blank=True,
            null=True,
            help_text="Additional HTTP headers for callback (JSON format, encrypted)"
        )
    )

    # Expiration
    expiring = models.DateTimeField(
        db_column="Expiring",
        null=True,
        blank=True,
        help_text="Subscription expiration date (optional)"
    )

    # Transaction tracking
    transaction_id = models.CharField(
        db_column="TransactionId",
        max_length=255,
        null=True,
        blank=True,
        help_text="Original transaction ID from subscribe request"
    )

    reference_id = models.CharField(
        db_column="ReferenceId",
        max_length=255,
        null=True,
        blank=True,
        help_text="Original reference ID from subscribe request"
    )

    class Meta:
        managed = True
        db_table = "tblDCISubscription"
        verbose_name = "DCI Subscription"
        verbose_name_plural = "DCI Subscriptions"
        indexes = [
            models.Index(fields=['subscription_code']),
            models.Index(fields=['sender_id']),
            models.Index(fields=['status']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"DCISubscription({self.subscription_code}, {self.sender_id}, {self.event_type})"

    def is_active(self):
        """Check if subscription is active and not expired"""
        if self.status != self.SubscriptionStatus.ACTIVE:
            return False

        if self.expiring:
            return ad_datetime.AdDatetime.now() < self.expiring

        return True


class DCINotificationLog(models.Model):
    """
    DCI Notification Log

    Tracks all notification attempts for audit and debugging.
    """

    id = models.UUIDField(
        primary_key=True,
        db_column="UUID",
        default=uuid.uuid4,
        editable=False
    )

    subscription = models.ForeignKey(
        DCISubscription,
        on_delete=models.CASCADE,
        related_name="notifications_sent",
        null=False,
        db_column="SubscriptionId"
    )

    # Notification details
    event_type = models.CharField(
        db_column="EventType",
        max_length=50,
        null=False
    )

    resource_type = models.CharField(
        db_column="ResourceType",
        max_length=100,
        null=False,
        help_text="Type of resource (Person, Farmer, Member)"
    )

    resource_id = models.CharField(
        db_column="ResourceId",
        max_length=255,
        null=False,
        help_text="ID of the affected resource"
    )

    # Notification result
    notified_successfully = models.BooleanField(
        db_column="NotifiedSuccessfully",
        null=False
    )

    notification_time = DateTimeField(
        db_column="NotificationTime",
        null=False,
        default=ad_datetime.AdDatetime.now
    )

    http_status_code = models.IntegerField(
        db_column="HttpStatusCode",
        null=True,
        blank=True
    )

    error = models.TextField(
        db_column="Error",
        blank=True,
        null=True
    )

    # Correlation
    correlation_id = models.CharField(
        db_column="CorrelationId",
        max_length=255,
        null=True,
        blank=True,
        help_text="Correlation ID for tracking notifications"
    )

    class Meta:
        managed = True
        db_table = "tblDCINotificationLog"
        verbose_name = "DCI Notification Log"
        verbose_name_plural = "DCI Notification Logs"
        indexes = [
            models.Index(fields=['subscription']),
            models.Index(fields=['notification_time']),
            models.Index(fields=['notified_successfully']),
            models.Index(fields=['correlation_id']),
        ]

    def __str__(self):
        status = "✓" if self.notified_successfully else "✗"
        return f"{status} {self.event_type} {self.resource_type}:{self.resource_id}"
