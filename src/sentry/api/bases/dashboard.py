from __future__ import absolute_import
from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
