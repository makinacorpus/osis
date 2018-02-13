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

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business.entity import get_entities_ids
from base.business.entity_version import SERVICE_COURSE
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.common import get_clean_data, treat_empty_or_str_none_as_none, TooManyResultsException
from base.models import entity_version as mdl_entity_version, learning_unit_year
from base.models.academic_year import AcademicYear, current_academic_year
from base.models.enums import entity_container_year_link_type, learning_container_year_types, \
    learning_unit_year_subtypes, active_status
from base.forms.utils.uppercase import convert_to_uppercase

MAX_RECORDS = 1000
ALL_CHOICES = ((None, _('all_label')),)


class LearningUnitYearForm(forms.Form):
    academic_year_id = forms.ModelChoiceField(
        label=_('academic_year_small'),
        queryset=AcademicYear.objects.all(),
        empty_label=_('all_label'),
        required=False
    )

    container_type = forms.ChoiceField(
        label=_('type'),
        choices=ALL_CHOICES + learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES,
        required=False
    )

    subtype = forms.ChoiceField(
        label=_('subtype'),
        choices=ALL_CHOICES + learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        required=False
    )

    status = forms.ChoiceField(
        label=_('status'),
        choices=ALL_CHOICES + active_status.ACTIVE_STATUS_LIST[:-1],
        required=False
    )

    acronym = forms.CharField(
        max_length=20,
        required=False,
        label=_('acronym')
    )

    title = forms.CharField(
        max_length=20,
        required=False,
        label=_('title')
    )

    requirement_entity_acronym = forms.CharField(
        max_length=20,
        required=False,
        label=_('requirement_entity_small')
    )

    allocation_entity_acronym = forms.CharField(
        max_length=20,
        required=False,
        label=_('allocation_entity_small')
    )

    with_entity_subordinated = forms.BooleanField(required=False, label=_('with_entity_subordinated_small'))

    def __init__(self, *args, **kwargs):
        self.service_course_search = kwargs.pop('service_course_search', False)
        super().__init__(*args, **kwargs)
        self.fields['academic_year_id'].initial = current_academic_year()

    def clean_acronym(self):
        data_cleaned = self.cleaned_data.get('acronym')
        data_cleaned = treat_empty_or_str_none_as_none(data_cleaned)
        if data_cleaned and learning_unit_year.check_if_acronym_regex_is_valid(data_cleaned) is None:
            raise ValidationError(_('LU_ERRORS_INVALID_REGEX_SYNTAX'))
        return data_cleaned

    def clean_requirement_entity_acronym(self):
        return convert_to_uppercase(self.cleaned_data.get('requirement_entity_acronym'))

    def clean_allocation_entity_acronym(self):
        data_cleaned = self.cleaned_data.get('allocation_entity_acronym')
        if data_cleaned:
            return data_cleaned.upper()
        return data_cleaned

    def clean(self):
        if not self.service_course_search \
                and self.cleaned_data and learning_unit_year.count_search_results(**self.cleaned_data) > MAX_RECORDS:
            raise TooManyResultsException
        return get_clean_data(self.cleaned_data)

    def get_activity_learning_units(self):
        if self.service_course_search:
            return self._get_service_course_learning_units()
        else:
            return self._get_learning_units()

    def _get_learning_units(self, service_course_search=None):
        clean_data = self.cleaned_data
        service_course_search = service_course_search or self.service_course_search

        parent_version_prefetch = Prefetch('parent__entityversion_set',
                                           queryset=mdl_entity_version.search(),
                                           to_attr='entity_versions')

        entity_version_prefetch = Prefetch('entity__entityversion_set',
                                           queryset=mdl_entity_version.search()
                                           .prefetch_related(parent_version_prefetch),
                                           to_attr='entity_versions')

        entity_container_prefetch = Prefetch('learning_container_year__entitycontaineryear_set',
                                             queryset=mdl.entity_container_year.search(
                                                 link_type=[entity_container_year_link_type.ALLOCATION_ENTITY,
                                                            entity_container_year_link_type.REQUIREMENT_ENTITY])
                                             .prefetch_related(entity_version_prefetch),
                                             to_attr='entity_containers_year')

        clean_data['learning_container_year_id'] = get_filter_learning_container_ids(clean_data)
        learning_units = mdl.learning_unit_year.search(**clean_data) \
            .select_related('academic_year', 'learning_container_year',
                            'learning_container_year__academic_year') \
            .prefetch_related(entity_container_prefetch) \
            .order_by('academic_year__year', 'acronym')

        return [append_latest_entities(learning_unit, service_course_search) for learning_unit in
                learning_units]

    def _get_service_course_learning_units(self):
        service_courses = []

        for learning_unit in self._get_learning_units(True):
            if not learning_unit.entities.get(SERVICE_COURSE):
                continue

            if self._is_matching_learning_unit(learning_unit):
                service_courses.append(learning_unit)

        return service_courses

    def _is_matching_learning_unit(self, learning_unit):
        allocation_entity_acronym = self.cleaned_data['allocation_entity_acronym']
        requirement_entity_acronym = self.cleaned_data['requirement_entity_acronym']

        allocation_entity_service_course = learning_unit.entities. \
            get(entity_container_year_link_type.ALLOCATION_ENTITY)

        requirement_entity_service_course = learning_unit.entities. \
            get(entity_container_year_link_type.REQUIREMENT_ENTITY)

        return allocation_entity_acronym in (
            allocation_entity_service_course.acronym, None
        ) and requirement_entity_acronym in (
            requirement_entity_service_course.acronym, None
        )


def get_filter_learning_container_ids(filter_data):
    requirement_entity_acronym = filter_data.get('requirement_entity_acronym')
    allocation_entity_acronym = filter_data.get('allocation_entity_acronym')
    with_entity_subordinated = filter_data.get('with_entity_subordinated', False)
    entities_id_list = []

    if requirement_entity_acronym:
        entity_ids = get_entities_ids(requirement_entity_acronym, with_entity_subordinated)

        entities_id_list += list(
            mdl.entity_container_year.search(
                link_type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                entity_id=entity_ids
            ).values_list(
                'learning_container_year', flat=True).distinct()
        )

    if allocation_entity_acronym:
        entity_ids = get_entities_ids(allocation_entity_acronym, False)
        entities_id_list += list(
            mdl.entity_container_year.search(
                link_type=entity_container_year_link_type.ALLOCATION_ENTITY,
                entity_id=entity_ids
            ).values_list(
                'learning_container_year', flat=True
            ).distinct()
        )

    return entities_id_list if entities_id_list else None
