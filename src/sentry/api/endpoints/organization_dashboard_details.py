from __future__ import absolute_import

from django.http import Http404
from rest_framework.response import Response

from sentry.api.bases.organization import (
    OrganizationEndpoint
)
from sentry.api.bases.dashboard import DashboardWithWidgetsSerializer
from sentry.api.serializers import serialize
from sentry.api.serializers.models.dashboard import DashboardWithWidgetsSerializer as DashboardModelSerializer
from sentry.models import Dashboard, Widget, WidgetDataSource


class OrganizationDashboardDetailsEndpoint(OrganizationEndpoint):

    def put(self, request, organization, dashboard_id):
        try:
            dashboard = Dashboard.objects.get(
                id=dashboard_id,
                organization_id=organization.id,
            )
        except Dashboard.DoesNotExist:
            raise Http404

        serializer = DashboardWithWidgetsSerializer(
            data=request.DATA,
            context={'organization': organization}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.object

        dashboard.update(
            title=data['title'],
            created_by=data['createdBy']
        )
        for widget_data in data['widgets']:
            widget, __created = Widget.objects.create_or_update(
                dashboard_id=dashboard_id,
                order=widget_data['order'],
                values={
                    'title': widget_data['title'],
                    'display_type': widget_data['displayType'],
                    'display_options': widget_data.get('displayOptions', {}),
                }
            )
            for data_source in widget_data['dataSources']:
                WidgetDataSource.objects.create_or_update(
                    widget_id=widget.id,
                    values={
                        'name': data_source['name'],
                        'data': data_source['data'],
                        'type': data_source['type'],
                    },
                    order=data_source['order'],
                )
        return self.respond(serialize(dashboard, request.user,
                                      DashboardModelSerializer()), status=200)
