from __future__ import absolute_import, print_function

from django.db import models
from django.utils import timezone
from uuid import uuid4

from sentry.constants import ObjectStatus
from sentry.db.models import (
    GUIDField,
    Model,
    BaseManager,
    BoundedPositiveIntegerField,
    EncryptedJsonField,
    EncryptedTextField,
    sane_repr,
)


def generate_secret():
    return uuid4().hex + uuid4().hex


class MonitorType(object):
    UNKNOWN = 0
    HEALTH_CHECK = 1
    HEARTBEAT = 2
    CRON_JOB = 3

    @classmethod
    def as_choices(cls):
        return (
            (cls.UNKNOWN, 'unknown'),
            (cls.HEALTH_CHECK, 'health_check'),
            (cls.HEARTBEAT, 'heartbeat'),
            (cls.CRON_JOB, 'cron_job'),
        )


class Monitor(Model):
    __core__ = True

    guid = GUIDField()
    project_id = BoundedPositiveIntegerField(db_index=True)
    name = models.CharField(max_length=128)
    status = BoundedPositiveIntegerField(
        default=0,
        choices=ObjectStatus.as_choices(),
    )
    type = BoundedPositiveIntegerField(
        default=0,
        choices=MonitorType.as_choices(),
    )
    secret = EncryptedTextField(default=generate_secret)
    config = EncryptedJsonField(default=dict)
    date_added = models.DateTimeField(default=timezone.now)
    objects = BaseManager(cache_fields=('guid', ))

    class Meta:
        app_label = 'sentry'
        db_table = 'sentry_monitor'

    __repr__ = sane_repr('guid', 'project_id', 'name')
