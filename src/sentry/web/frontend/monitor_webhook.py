from __future__ import absolute_import, print_function

import hmac
import logging
from hashlib import sha256
from simplejson import JSONDecodeError

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.utils import timezone

from sentry.api import client
from sentry.models import Monitor
from sentry.utils import json


class MonitorWebhookView(View):
    def verify(self, monitor_id, token, signature):
        return constant_time_compare(signature, hmac.new(
            key=str(token),
            msg=str(monitor_id),
            digestmod=sha256
        ).hexdigest())

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(MonitorWebhookView, self).dispatch(*args, **kwargs)

    def post(self, request, monitor_id, signature):
        monitor = Monitor.objects.get_from_cache(
            id=monitor_id,
        )

        if not self.verify(monitor_id, token, signature):
            logging.warn('Unable to verify signature for monitor webhook (%s)',
                         monitor_id)
            return HttpResponse(status=403)

        monitor.update(last_checkin=timezone.now())
        return HttpResponse(
            status=resp.status_code,
            content=json.dumps(resp.data),
            content_type='application/json',
        )
