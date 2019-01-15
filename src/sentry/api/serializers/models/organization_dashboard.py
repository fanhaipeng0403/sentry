from __future__ import absolute_import

import six
from sentry.api.serializers import Serializer, register
from sentry.models import Dashboard


@register(Dashboard)
class DashboardSerializer(Serializer):

    def serialize(self, obj, attrs, user, *args, **kwargs):
        data = {
            'id': six.text_type(obj.id),
            'title': obj.title,
            'organization': six.text_type(obj.organization.id),
            'dateAdded': obj.date_added,
            'created_by': six.text_type(obj.created_by.id),
        }

        return data
