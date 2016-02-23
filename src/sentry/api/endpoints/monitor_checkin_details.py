from __future__ import absolute_import

from rest_framework import serializers

from sentry import features
from sentry.api.base import Endpoint, ResourceDoesNotExist
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

    def convert_args(self, request, monitor_id, checkin_id, *args, **kwargs):
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

        try:
            checkin = MonitorCheckIn.objects.get(
                monitor=monitor,
                id=id,
            )
        except MonitorCheckIn.DoesNotExist:
            raise ResourceDoesNotExist

        request._request.organization = project.organization

        kwargs.update({
            'checkin': checkin,
            'project': project,
        })
        return (args, kwargs)

    def get(self, request, project, checkin):
        """
        Retrieve a check-in
        ``````````````````

        :pparam string monitor_id: the id of the monitor.
        :pparam string checkin_id: the id of the check-in.
        :auth: required
        """
        return self.respond(serialize(checkin, request.user))

    def put(self, request, project, checkin):
        """
        Update a check-in
        `````````````````

        :pparam string monitor_id: the id of the monitor.
        :pparam string checkin_id: the id of the check-in.
        :auth: required
        """
        serializer = CheckInSerializer(
            data=request.DATA,
            partial=True,
            context={
                'project': project,
                'request': request,
            },
        )
        if not serializer.is_valid():
            return self.respond(serializer.errors, status=400)

        result = serializer.object

        params = {}
        if 'duration' in result:
            params['duration'] = result['duration']
        if 'status' in result:
            params['status'] = getattr(CheckInStatus, result['status'])
        if params:
            checkin.update(**params)

        return self.respond(serialize(checkin, request.user))
