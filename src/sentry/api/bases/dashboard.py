from __future__ import absolute_import
from rest_framework import serializers
from sentry.api.fields.user import UserField


class DashboardSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    created_by = UserField(required=True)
