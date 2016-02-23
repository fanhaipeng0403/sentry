from __future__ import absolute_import

from rest_framework import serializers

from sentry import features
from sentry.api.base import Endpoint, ResourceDoesNotExist
from sentry.api.paginator import OffsetPaginator
from sentry.api.bases.project import ProjectPermission
from sentry.api.serializers import serialize
from sentry.models import Monitor, MonitorCheckIn, CheckInStatus, ProjectStatus
from sentry.utils.sdk import configure_scope


class CheckInSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=tuple(
            (k, k) for k in (CheckInStatus.SUCCESS, CheckInStatus.FAILURE, CheckInStatus.IN_PROGRESS)
        )
    )
    duration = serializers.IntegerField(required=False)


class MonitorCheckInsEndpoint(Endpoint):
    # TODO(dcramer): this code needs shared with other endpoints as its security focused
    # TODO(dcramer): this doesnt handle is_global roles
    permission_classes = (ProjectPermission,)

    def convert_args(self, request, monitor_id, *args, **kwargs):
        try:
            monitor = Monitor.objects.get(
                id=monitor_id,
            )
        except Monitor.DoesNotExist:
            raise ResourceDoesNotExist

        project = monitor.project
        if project.status != ProjectStatus.VISIBLE:
            raise ResourceDoesNotExist

        if not features.has('organizations:monitors',
                            project.organization, actor=request.user):
            raise ResourceDoesNotExist

        self.check_object_permissions(request, project)

        with configure_scope() as scope:
            scope.set_tag("organization", project.organization_id)
            scope.set_tag("project", project.id)

        request._request.organization = project.organization

        kwargs.update({
            'monitor': monitor,
            'project': project,
        })
        return (args, kwargs)

    def get(self, request, project, monitor):
        """
        Retrieve check-ins for an monitor
        `````````````````````````````````

        :pparam string monitor_id: the id of the monitor.
        :auth: required
        """
        queryset = MonitorCheckIn.objects.filter(
            monitor_id=monitor.id,
        )

        return self.paginate(
            request=request,
            queryset=queryset,
            order_by='name',
            on_results=lambda x: serialize(x, request.user),
            paginator_cls=OffsetPaginator,
        )

    def post(self, request, project, monitor):
        """
        Create a new check-in for a monitor
        ```````````````````````````````````

        :pparam string monitor_id: the id of the monitor.
        :auth: required
        """
        serializer = CheckInSerializer(
            data=request.DATA,
            context={
                'project': project,
                'request': request,
            },
        )
        if not serializer.is_valid():
            return self.respond(serializer.errors, status=400)

        result = serializer.object

        checkin = MonitorCheckIn.objects.filter(
            project_id=project.id,
            monitor_id=monitor.id,
            duration=result.get('duration'),
            status=getattr(CheckInStatus, result['status']),
        )

        return self.respond(serialize(checkin, request.user))
