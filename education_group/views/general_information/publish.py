from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.business.education_groups.general_information import PublishException
from base.views.common import display_error_messages, display_success_messages
from education_group.ddd import command
from education_group.ddd.service.write import publish_common_pedagogy_service, publish_common_admission_service


@login_required
@require_http_methods(['POST'])
def publish_common_admission(request, year, redirect_view):
    try:
        cmd = command.PublishCommonAdmissionCommand(year=year)
        publish_common_admission_service.publish_common_admission(cmd)
        display_success_messages(request, _('Common admission will be published soon'))
    except PublishException as e:
        display_error_messages(request, str(e))
    return HttpResponseRedirect(reverse(redirect_view, kwargs={'year': year}))


@login_required
@require_http_methods(['POST'])
def publish_common_pedagogy(request, year):
    try:
        cmd = command.PublishCommonPedagogyCommand(year=year)
        publish_common_pedagogy_service.publish_common_pedagogy(cmd)
        display_success_messages(request, _('Common general informations will be published soon'))
    except PublishException as e:
        display_error_messages(request, str(e))
    return HttpResponseRedirect(reverse('common_general_information', kwargs={'year': year}))
