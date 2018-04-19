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
from django.db import IntegrityError
from django.forms import formset_factory
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit import SERVICE_COURSES_SEARCH, create_xls, SIMPLE_SEARCH
from base.forms.common import TooManyResultsException
from base.forms.learning_unit.search_form import LearningUnitYearForm, MAX_RECORDS
from base.forms.proposal.learning_unit_proposal import LearningUnitProposalForm, ProposalRowForm, ProposalListFormset
from base.models.academic_year import current_academic_year, get_last_academic_years
from base.models.enums import learning_container_year_types, learning_unit_year_subtypes
from base.models.person import Person, find_by_user
from base.views import layout
from base.views.common import check_if_display_message, display_error_messages, display_success_messages, \
    display_messages_by_level
from base.business import learning_unit_proposal as proposal_business

PROPOSAL_SEARCH = 3
SUMMARY_LIST = 4


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
def learning_units(request):
    return learning_units_search(request, SIMPLE_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_service_course(request):
    return learning_units_search(request, SERVICE_COURSES_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_proposal_search(request):
    search_form = LearningUnitProposalForm(request.GET or None)
    proposals = []
    try:
        if search_form.is_valid():
            proposals = search_form.get_proposal_learning_units()
            check_if_display_message(request, proposals)

    except TooManyResultsException:
        display_error_messages(request, 'too_many_results')

    if proposals:
        proposals = _proposal_management(request, proposals)
    a_person = find_by_user(request.user)
    context = {
        'form': search_form,
        'academic_years': get_last_academic_years(),
        'current_academic_year': current_academic_year(),
        'experimental_phase': True,
        'search_type': PROPOSAL_SEARCH,
        'proposals': proposals,
        'is_faculty_manager': a_person.is_faculty_manager()
    }

    return layout.render(request, "learning_units.html", context)


def _proposal_management(request, proposals):
    list_proposal_formset = formset_factory(form=ProposalRowForm, formset=ProposalListFormset,
                                            extra=len(proposals), max_num=MAX_RECORDS)

    formset = list_proposal_formset(request.POST or None,
                                    list_proposal_learning=proposals,
                                    action=request.POST.get('action') if request.POST else None)
    return process_formset(formset, request)


def process_formset(formset, request):
    if formset.is_valid():
        if formset.action == 'back_to_initial':
            formset = _go_back_to_initial_data(formset, request)
        elif formset.action == "consolidate":
            _consolidate_proposals(formset, request)
        else:
            _force_state(formset, request)
    return formset


def _go_back_to_initial_data(formset, request):
    return _apply_action_on_proposals(formset, request, proposal_business.cancel_proposals)


def _consolidate_proposals(formset, request):
    return _apply_action_on_proposals(formset, request, proposal_business.consolidate_proposals)


def _apply_action_on_proposals(formset, request, action_method):
    proposals = formset.get_checked_proposals()
    if proposals:
        user_person = get_object_or_404(Person, user=request.user)
        messages_by_level = action_method(proposals, user_person)
        display_messages_by_level(request, messages_by_level)
        formset = None
    else:
        _build_no_data_error_message(request)
    return formset


def _build_no_data_error_message(request):
    display_error_messages(request, _("error_proposal_no_data"))


def _force_state(formset, request):
    try:
        formset.save()
        display_success_messages(request, _("proposal_edited_successfully"))
    except IntegrityError:
        display_error_messages(request, _("error_modification_learning_unit"))
