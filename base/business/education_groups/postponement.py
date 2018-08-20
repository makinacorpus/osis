##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.forms import model_to_dict

from base import models as mdl_base
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear

EDUCATION_GROUP_MAX_POSTPONE_YEARS = 6


def start(education_group, start_year):
    postpone_list = []

    base_education_group_year = _get_start_education_group_year(education_group, start_year)
    if not base_education_group_year:
        return postpone_list

    end_year = _compute_end_year(education_group)
    for academic_year in mdl_base.academic_year.find_academic_years(start_year=start_year + 1, end_year=end_year):
        postponed_egy = _postpone_education_group_year(base_education_group_year, academic_year)
        postpone_list.append(postponed_egy)
    return postpone_list


def _get_start_education_group_year(education_group, start_year):
    try:
        return EducationGroupYear.objects.get(
            education_group=education_group,
            academic_year__year=start_year
        )
    except EducationGroupYear.DoesNotExist:
        return None


def _compute_end_year(education_group):
    """
        This function compute the end year that the postponement must achieve
        :arg education_group: The education group that we want to postpone
    """
    # Compute max postponement based on config EDUCATION_GROUP_MAX_POSTPONE_YEARS
    max_postponement_end_year = mdl_base.academic_year.current_academic_year().year + EDUCATION_GROUP_MAX_POSTPONE_YEARS
    if education_group.end_year:
        # Get the min [Prevent education_group.end_year > academic_year.year provided by system]
        max_postponement_end_year = min(max_postponement_end_year, education_group.end_year)

    # Lookup on database, get the latest existing education group year [Prevent desync end_date and data]
    latest_egy = EducationGroupYear.objects.filter(education_group=education_group) \
                                           .select_related('academic_year') \
                                           .order_by('academic_year__year')\
                                           .last()
    return max(max_postponement_end_year, latest_egy.academic_year.year)


def _postpone_education_group_year(education_group_year, academic_year):
    """
    This function will postpone the education group year in the academic year given as params
    """
    # Postpone the education group year
    field_to_exclude = ['id', 'external_id', 'academic_year', 'languages', 'secondary_domains']
    egy_to_postpone = _model_to_dict(education_group_year, exclude=field_to_exclude)
    postponed_egy, created = EducationGroupYear.objects.update_or_create(
        education_group=education_group_year.education_group,
        academic_year=academic_year,
        defaults=egy_to_postpone
    )
    # Postpone the m2m [languages / secondary_domains]
    _postpone_m2m(education_group_year, postponed_egy)
    return postponed_egy


def _model_to_dict(instance, exclude=None):
    """
    It allows to transform an instance to a dict and for each FK, it add '_id'
    This function is based on model_to_dict implementation.
    """
    data = model_to_dict(instance, exclude=exclude)

    opts = instance._meta
    for fk_field in filter(lambda field: field.is_relation, opts.concrete_fields):
        if fk_field.name in data:
            data[fk_field.name + "_id"] = data.pop(fk_field.name)
    return data


def _postpone_m2m(education_group_year, postponed_egy):
    fields_to_exclude = []

    opts = education_group_year._meta
    for f in opts.many_to_many:
        if f.name in fields_to_exclude:
            continue
        m2m_cls = f.rel.through

        # Remove records of posptponed_egy
        m2m_cls.objects.all().filter(education_group_year=postponed_egy).delete()

        # Recreate records
        for m2m_obj in m2m_cls.objects.all().filter(education_group_year_id=education_group_year):
            m2m_data_to_postpone = _model_to_dict(m2m_obj, exclude=['id', 'external_id', 'education_group_year'])
            m2m_cls(education_group_year=postponed_egy, **m2m_data_to_postpone).save()


class PostponementEducationGroupYearMixin:
    """
    This mixin will report the modification to the futures years.

    If one of the future year is already modified, it will stop the postponement and append a warning message
    """

    # Postpone the education group year
    field_to_exclude = ['id', 'external_id', 'academic_year', 'languages', 'secondary_domains']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.postpone_start_year = None
        self.postpone_end_year = None
        self.education_group_year_postponed = []
        self.postponement_errors = {}
        self.warnings = []

        if not self._is_creation():
            self.dict_initial_egy = _model_to_dict(
                self.forms[forms.ModelForm].instance, exclude=self.field_to_exclude
            )

    def save(self):
        education_group_year = super().save()

        self.postpone_start_year = education_group_year.academic_year.year
        self.postpone_end_year = _compute_end_year(education_group_year.education_group)
        self._start_postponement(education_group_year)

        return education_group_year

    def _start_postponement(self, education_group_year):
        dict_new_value = _model_to_dict(education_group_year, exclude=self.field_to_exclude)

        for academic_year in AcademicYear.objects.filter(year__gt=self.postpone_start_year,
                                                         year__lte=self.postpone_end_year):

            postponed_egy, created = EducationGroupYear.objects.get_or_create(
                education_group=education_group_year.education_group,
                academic_year=academic_year,
                defaults=self.dict_initial_egy
            )

            if not created:
                dict_postponsed_egy = _model_to_dict(postponed_egy, exclude=self.field_to_exclude)

                differences = self.compare_objects(dict_postponsed_egy)
                if differences:
                    self.add_postponement_errors(postponed_egy, differences)
                    break

            self.update_object(postponed_egy, dict_new_value)
            # Postpone the m2m [languages / secondary_domains]
            _postpone_m2m(education_group_year, postponed_egy)

            self.education_group_year_postponed.append(postponed_egy)

    def compare_objects(self, current_dict):
        return {x: current_dict[x] for x in self.dict_initial_egy if self.dict_initial_egy[x] != current_dict[x]}

    @staticmethod
    def update_object(education_group_year, new_values):
        for attr, value in new_values.items():
            setattr(education_group_year, attr, value)
        return education_group_year.save()

    def add_postponement_errors(self, postponed_education_group_year, differences):
        self.warnings.append("Impossible to save {}. It has been already modify ({})".format(
            str(postponed_education_group_year),
            str(differences))
        )
