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
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from base.business.learning_units import perms as business_perms

from base.models import learning_unit_year, person, proposal_learning_unit
from base.models.proposal_learning_unit import ProposalLearningUnit


def can_delete_learning_unit_year(view_func):
    def f_can_delete_learning_unit_year(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)
        if not business_perms.can_delete_learning_unit_year(learn_unit_year, pers):
            raise PermissionDenied
        return view_func(request, learning_unit_year_id)
    return f_can_delete_learning_unit_year


def can_create_partim(view_func):
    def f_can_create_partim(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)
        if not business_perms.is_person_linked_to_entity_in_charge_of_learning_unit(learn_unit_year, pers):
            raise PermissionDenied
        return view_func(request, learning_unit_year_id)
    return f_can_create_partim


def can_create_modification_proposal(view_func):
    def f_can_perform_modification_proposal(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)
        if not business_perms.is_eligible_to_create_modification_proposal(learn_unit_year, pers):
            raise PermissionDenied("Learning unit year not eligible for proposal or user has not sufficient rights.")
        return view_func(request, learning_unit_year_id)
    return f_can_perform_modification_proposal


def can_edit_learning_unit_proposal(view_func):
    def f_can_edit_learning_unit_proposal(request, learning_unit_year_id):
        proposal = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)

        if not business_perms.is_eligible_to_edit_proposal(proposal, pers):
            raise PermissionDenied(
                "User has not sufficient rights to edit proposal."
            )
        return view_func(request, learning_unit_year_id)
    return f_can_edit_learning_unit_proposal


def can_perform_cancel_proposal(view_func):
    def f_can_perform_cancel_proposal(request, learning_unit_year_id):
        learning_unit_proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year__id=learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)
        if not business_perms.is_eligible_for_cancel_of_proposal(learning_unit_proposal, pers):
            raise PermissionDenied("Learning unit proposal cannot be cancelled.")
        return view_func(request, learning_unit_year_id)
    return f_can_perform_cancel_proposal


def can_perform_end_date_modification(view_func):
    def f_can_perform_end_date_modification(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)
        if not business_perms.is_eligible_for_modification_end_date(learn_unit_year, pers):
            raise PermissionDenied("Learning unit year date is not editable or user has not sufficient rights.")
        return view_func(request, learning_unit_year_id)
    return f_can_perform_end_date_modification


def can_perform_learning_unit_modification(view_func):
    def f_can_perform_learning_unit_modification(request, learning_unit_year_id, *args, **kwargs):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(person.Person, user=request.user)
        if not business_perms.is_eligible_for_modification(learn_unit_year, pers):
            raise PermissionDenied("Learning unit year cannot be modified.")
        return view_func(request, learning_unit_year_id, *args, **kwargs)
    return f_can_perform_learning_unit_modification
