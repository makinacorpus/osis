##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.messages import WARNING
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit import SERVICE_COURSES_SEARCH, create_xls, SIMPLE_SEARCH
from base.decorators import cache_filter
from base.forms.common import TooManyResultsException
from base.forms.learning_unit.search_form import LearningUnitYearForm
from base.forms.proposal.learning_unit_proposal import LearningUnitProposalForm, ProposalStateModelForm
from base.models.academic_year import current_academic_year, get_last_academic_years
from base.models.enums import learning_container_year_types, learning_unit_year_subtypes
from base.models.person import Person, find_by_user
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views import layout
from base.views.common import check_if_display_message, display_error_messages, display_messages_by_level
from base.business import learning_unit_proposal as proposal_business

PROPOSAL_SEARCH = 3
SUMMARY_LIST = 4

ACTION_BACK_TO_INITIAL = "back_to_initial"
ACTION_CONSOLIDATE = "consolidate"
ACTION_FORCE_STATE = "force_state"


def learning_units_search(request, search_type):
    service_course_search = search_type == SERVICE_COURSES_SEARCH

    form = LearningUnitYearForm(request.GET or None, service_course_search=service_course_search)
    found_learning_units = []
    try:
        if form.is_valid():
            found_learning_units = form.get_activity_learning_units()

            check_if_display_message(request, found_learning_units)
    except TooManyResultsException:
        messages.add_message(request, messages.ERROR, _('too_many_results'))

    if request.GET.get('xls_status') == "xls":
        return create_xls(request.user, found_learning_units)
    a_person = find_by_user(request.user)
    context = {
        'form': form,
        'academic_years': get_last_academic_years(),
        'container_types': learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES,
        'types': learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        'learning_units': found_learning_units,
        'current_academic_year': current_academic_year(),
        'experimental_phase': True,
        'search_type': search_type,
        'is_faculty_manager': a_person.is_faculty_manager()
    }
    return layout.render(request, "learning_units.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units(request):
    return learning_units_search(request, SIMPLE_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units_service_course(request):
    return learning_units_search(request, SERVICE_COURSES_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_proposal_search(request):
    search_form = LearningUnitProposalForm(request.GET or None)
    user_person = get_object_or_404(Person, user=request.user)
    proposals = []
    research_criteria = []
    try:
        if search_form.is_valid():
            research_criteria = search_form.get_research_criteria()
            proposals = search_form.get_proposal_learning_units()
    except TooManyResultsException:
        display_error_messages(request, 'too_many_results')

    if request.POST:
        selected_proposals_id = request.POST.getlist("selected_action", default=[])
        selected_proposals = ProposalLearningUnit.objects.filter(id__in=selected_proposals_id)
        messages_by_level = apply_action_on_proposals(selected_proposals, user_person, request.POST, research_criteria)
        display_messages_by_level(request, messages_by_level)
        return redirect(reverse("learning_unit_proposal_search") + "?{}".format(request.GET.urlencode()))

    check_if_display_message(request, proposals)
    context = {'form': search_form, 'form_proposal_state': ProposalStateModelForm(),
               'academic_years': get_last_academic_years(), 'current_academic_year': current_academic_year(),
               'experimental_phase': True, 'search_type': PROPOSAL_SEARCH, 'proposals': proposals,
               'is_faculty_manager': user_person.is_faculty_manager()}

    return layout.render(request, "learning_units.html", context)


def apply_action_on_proposals(proposals, author, post_data, research_criteria):
    if not bool(proposals):
        return {WARNING: [_("No proposals was selected.")]}

    action = post_data.get("action", "")
    messages_by_level = {}
    if action == ACTION_BACK_TO_INITIAL:
        messages_by_level = proposal_business.cancel_proposals_and_send_report(proposals, author, research_criteria)
    elif action == ACTION_CONSOLIDATE:
        messages_by_level = proposal_business.consolidate_proposals_and_send_report(proposals, author,
                                                                                    research_criteria)
    elif action == ACTION_FORCE_STATE:
        form = ProposalStateModelForm(post_data)
        if form.is_valid():
            new_state = form.cleaned_data.get("state")
            messages_by_level = proposal_business.force_state_of_proposals(proposals, author, new_state)
    return messages_by_level
