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
import datetime
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from attribution.models import attribution_new

from attribution.models.attribution import Attribution
from base import models as mdl_base
from base.business.entity import get_entity_calendar, get_entities_ids, get_entity_container_list, \
    build_entity_container_prefetch
from base.business.learning_unit_year_with_context import volume_learning_component_year
from base.business.learning_units.simple.creation import create_learning_unit_content
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm
from base.models import entity_container_year, learning_unit_year
from base.models.academic_year import current_academic_year
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import entity_container_year_link_type, academic_calendar_type
from base.models.enums import learning_container_year_types
from cms import models as mdl_cms
from cms.enums import entity_name
# List of key that a user can modify
from cms.models import translated_text
from osis_common.document import xls_build
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from base.models.academic_year import find_academic_year_by_year
from osis_common.utils.datetime import convert_date_to_datetime

CMS_LABEL_SPECIFICATIONS = ['themes_discussed', 'skills_to_be_acquired', 'prerequisite']
CMS_LABEL_PEDAGOGY = ['resume', 'bibliography', 'teaching_methods', 'evaluation_methods',
                      'other_informations', 'online_resources']
CMS_LABEL_SUMMARY = ['resume']

SIMPLE_SEARCH = 1
SERVICE_COURSES_SEARCH = 2

LEARNING_UNIT_CREATION_SPAN_YEARS = 6


def get_last_academic_years(last_years=10):
    today = datetime.date.today()
    date_ten_years_before = today.replace(year=today.year - last_years)
    return mdl_base.academic_year.find_academic_years().filter(start_date__gte=date_ten_years_before)


def get_same_container_year_components(learning_unit_year, with_classes=False):
    learning_container_year = learning_unit_year.learning_container_year
    components = []
    learning_components_year = mdl_base.learning_component_year.find_by_learning_container_year(learning_container_year,
                                                                                                with_classes)
    additionnal_entities = {}

    for indx, learning_component_year in enumerate(learning_components_year):
        if learning_component_year.classes:
            for learning_class_year in learning_component_year.classes:
                learning_class_year.used_by_learning_units_year = _learning_unit_usage_by_class(learning_class_year)
                learning_class_year.is_used_by_full_learning_unit_year = _is_used_by_full_learning_unit_year(
                    learning_class_year)

        used_by_learning_unit = mdl_base.learning_unit_component.search(learning_component_year, learning_unit_year)

        entity_components_yr = EntityComponentYear.objects.filter(learning_component_year=learning_component_year)
        if indx == 0:
            additionnal_entities = _get_entities(entity_components_yr)

        components.append({'learning_component_year': learning_component_year,
                           'volumes': volume_learning_component_year(learning_component_year, entity_components_yr),
                           'learning_unit_usage': _learning_unit_usage(learning_component_year),
                           'used_by_learning_unit': used_by_learning_unit
                           })

    return _compose_components_dict(components, additionnal_entities)


def show_subtype(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year

    if learning_container_year:
        return learning_container_year.container_type == learning_container_year_types.COURSE or \
               learning_container_year.container_type == learning_container_year_types.INTERNSHIP
    return False


def get_campus_from_learning_unit_year(learning_unit_year):
    if learning_unit_year.learning_container_year:
        return learning_unit_year.learning_container_year.campus


def get_organization_from_learning_unit_year(learning_unit_year):
    campus = get_campus_from_learning_unit_year(learning_unit_year)
    if campus:
        return campus.organization


def get_all_attributions(learning_unit_year):
    attributions = {}
    if learning_unit_year.learning_container_year:
        all_attributions = entity_container_year.find_last_entity_version_grouped_by_linktypes(
            learning_unit_year.learning_container_year)

        attributions['requirement_entity'] = all_attributions.get(entity_container_year_link_type.REQUIREMENT_ENTITY)
        attributions['allocation_entity'] = all_attributions.get(entity_container_year_link_type.ALLOCATION_ENTITY)
        attributions['additional_requirement_entity_1'] = \
            all_attributions.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)
        attributions['additional_requirement_entity_2'] = \
            all_attributions.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
    return attributions


def get_cms_label_data(cms_label, user_language):
    cms_label_data = OrderedDict()
    translated_labels = mdl_cms.translated_text_label.search(text_entity=entity_name.LEARNING_UNIT_YEAR,
                                                             labels=cms_label,
                                                             language=user_language)

    for label in cms_label:
        translated_text = next((trans.label for trans in translated_labels if trans.text_label.label == label), None)
        cms_label_data[label] = translated_text

    return cms_label_data


def _learning_unit_usage(a_learning_component_year):
    components = mdl_base.learning_unit_component.find_by_learning_component_year(a_learning_component_year)
    return ", ".join(["{} ({})".format(c.learning_unit_year.acronym, c.learning_unit_year.quadrimester or '?')
                      for c in components])


def _learning_unit_usage_by_class(a_learning_class_year):
    queryset = mdl_base.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year) \
        .order_by('learning_unit_component__learning_unit_year__acronym') \
        .values_list('learning_unit_component__learning_unit_year__acronym', flat=True)
    return ", ".join(list(queryset))


def get_components_identification(learning_unit_yr):
    a_learning_container_yr = learning_unit_yr.learning_container_year
    components = []
    additionnal_entities = {}

    if a_learning_container_yr:
        learning_component_year_list = mdl_base.learning_component_year.find_by_learning_container_year(
            a_learning_container_yr)

        for indx, learning_component_year in enumerate(learning_component_year_list):
            if mdl_base.learning_unit_component.search(learning_component_year, learning_unit_yr).exists():
                entity_components_yr = EntityComponentYear.objects.filter(
                    learning_component_year=learning_component_year)
                if indx == 0:
                    additionnal_entities = _get_entities(entity_components_yr)

                components.append({'learning_component_year': learning_component_year,
                                   'entity_component_yr': entity_components_yr.first(),
                                   'volumes': volume_learning_component_year(learning_component_year,
                                                                             entity_components_yr)})

    return _compose_components_dict(components, additionnal_entities)


def _is_used_by_full_learning_unit_year(a_learning_class_year):
    for l in mdl_base.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year):
        if l.learning_unit_component.learning_unit_year.subdivision is None:
            return True

    return False


def compute_max_academic_year_adjournment():
    starting_academic_year = mdl_base.academic_year.starting_academic_year()
    return starting_academic_year.year + LEARNING_UNIT_CREATION_SPAN_YEARS


def prepare_xls_content(found_learning_units):
    return [_extract_xls_data_from_learning_unit(lu) for lu in found_learning_units]


def _extract_xls_data_from_learning_unit(learning_unit_yr):
    return [learning_unit_yr.academic_year.name, learning_unit_yr.acronym, learning_unit_yr.complete_title,
            xls_build.translate(learning_unit_yr.learning_container_year.container_type),
            xls_build.translate(learning_unit_yr.subtype),
            _get_entity_acronym(learning_unit_yr.entities.get('REQUIREMENT_ENTITY')),
            _get_entity_acronym(learning_unit_yr.entities.get('ALLOCATION_ENTITY')),
            learning_unit_yr.credits, xls_build.translate(learning_unit_yr.status)]


def prepare_xls_parameters_list(user, workingsheets_data):
    return {xls_build.LIST_DESCRIPTION_KEY: "Liste d'activités",
            xls_build.FILENAME_KEY: 'Learning_units',
            xls_build.USER_KEY: _get_name_or_username(user),
            xls_build.WORKSHEETS_DATA:
                [{xls_build.CONTENT_KEY: workingsheets_data,
                  xls_build.HEADER_TITLES_KEY: [str(_('academic_year_small')),
                                                str(_('code')),
                                                str(_('title')),
                                                str(_('type')),
                                                str(_('subtype')),
                                                str(_('requirement_entity_small')),
                                                str(_('allocation_entity_small')),
                                                str(_('credits')),
                                                str(_('active_title'))],
                  xls_build.WORKSHEET_TITLE_KEY: 'Learning_units',
                  }
                 ]}


def _get_name_or_username(a_user):
    person = mdl_base.person.find_by_user(a_user)
    return "{}, {}".format(person.last_name, person.first_name) if person else a_user.username


def _get_entity_acronym(an_entity):
    return an_entity.acronym if an_entity else None


def create_xls(user, found_learning_units):
    workingsheets_data = prepare_xls_content(found_learning_units)
    return xls_build.generate_xls(prepare_xls_parameters_list(user, workingsheets_data))


def create_learning_unit_partim_structure(data_dict):
    learning_container = data_dict.get('learning_container', None)
    academic_year = data_dict.get('academic_year', None)
    learning_container_year = mdl_base.learning_container_year.search(academic_year, learning_container).get()
    return create_partim(data_dict, learning_container_year)


def create_partim(data_dict, new_learning_container_year):
    data = data_dict.get('data', None)
    new_learning_unit = data_dict.get('new_learning_unit', None)
    status = data_dict.get('status', None)
    academic_year = data_dict.get('academic_year', None)

    # Get all requirement entity containers [Min 1 - Max 3]
    requirement_entity_containers = list(entity_container_year.search(
        learning_container_year=new_learning_container_year,
        link_type=[entity_container_year_link_type.REQUIREMENT_ENTITY,
                   entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                   entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2]))

    return create_learning_unit_content({'academic_year': academic_year,
                                         'data': data,
                                         'new_learning_container_year': new_learning_container_year,
                                         'new_learning_unit': new_learning_unit,
                                         'requirement_entity_containers': requirement_entity_containers,
                                         'status': status})


def is_summary_submission_opened():
    current_academic_year = mdl_base.academic_year.current_academic_year()
    return mdl_base.academic_calendar.is_academic_calendar_opened(current_academic_year,
                                                                  academic_calendar_type.SUMMARY_COURSE_SUBMISSION)


def can_access_summary(user, learning_unit_year):
    try:
        get_object_or_404(Attribution, learning_unit_year=learning_unit_year,
                          tutor__person__user=user, summary_responsible=True)
    except Http404:
        raise PermissionDenied()
    return True


def initialize_learning_unit_pedagogy_form(learning_unit_year, language_code):
    lang = find_language_in_settings(language_code)
    return LearningUnitPedagogyForm(learning_unit_year=learning_unit_year, language=lang)


def find_language_in_settings(language_code):
    return next((lang for lang in settings.LANGUAGES if lang[0] == language_code), None)


def can_edit_summary_editable_field(person, is_person_linked_to_entity):
    return person.is_faculty_manager() and is_person_linked_to_entity


def _compose_components_dict(components, additional_entities):
    data_components = {'components': components}
    data_components.update(additional_entities)
    return data_components


def _get_entities(entity_components_yr):
    additional_requirement_entities_types = [entity_container_year_link_type.REQUIREMENT_ENTITY,
                                             entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                                             entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2]

    return {e.entity_container_year.type: e.entity_container_year.entity.most_recent_acronym
            for e in entity_components_yr
            if e.entity_container_year.type in additional_requirement_entities_types}


def get_learning_units_and_summary_status(a_person, academic_yr):
    entities_version_attached = a_person.find_main_entities_version
    learning_units_found = []
    # TODO : We must improve performance.
    cms_list = translated_text.find_with_changed(LEARNING_UNIT_YEAR, CMS_LABEL_PEDAGOGY)
    for an_entity_version in entities_version_attached:
        learning_units_found.extend(_get_learning_unit_by_entity(academic_yr, an_entity_version, cms_list))
    return learning_units_found


def _get_learning_unit_by_entity(academic_yr, an_entity_version, cms_list):
    a_calendar = _get_calendar(academic_yr, an_entity_version)
    if a_calendar:
        entity_learning_unit_yr_list = get_list_entity_learning_unit_yr(an_entity_version, academic_yr)
        if entity_learning_unit_yr_list:
            return _get_summary_detail(a_calendar, cms_list, entity_learning_unit_yr_list)
    return []


def get_list_entity_learning_unit_yr(an_entity_version, current_academic_yr):
    entity_ids = get_entities_ids(an_entity_version.entity.most_recent_acronym, False)
    entities_id_list = get_entity_container_list([], entity_ids, entity_container_year_link_type.REQUIREMENT_ENTITY)

    return learning_unit_year.search(**{'learning_container_year_id': entities_id_list,
                                        'academic_year_id': current_academic_yr,
                                        'status': True}) \
        .select_related('academic_year', 'learning_container_year',
                        'learning_container_year__academic_year') \
        .prefetch_related(build_entity_container_prefetch()) \
        .order_by('academic_year__year', 'acronym')


def _get_summary_status(a_calendar, cms_list, lu):
    for educational_information in cms_list:
        if educational_information.reference == lu.id \
                and _changed_in_period(a_calendar.start_date, a_calendar.end_date, educational_information.changed):
            return True
    return False


def _get_calendar(academic_yr, an_entity_version):
    a_calendar = get_entity_calendar(an_entity_version, academic_yr)
    if a_calendar is None:
        an_academic_calendar = find_academic_year_by_year(academic_yr.year)
        if an_academic_calendar:
            return an_academic_calendar
    return a_calendar


def _get_summary_detail(a_calendar, cms_list, entity_learning_unit_yr_list_param):
    entity_learning_unit_yr_list = entity_learning_unit_yr_list_param
    for lu in entity_learning_unit_yr_list:
        lu.summary_responsibles = attribution_new.search(summary_responsible=True,
                                                         learning_container_year=lu.learning_container_year)
        lu.summary_status = _get_summary_status(a_calendar, cms_list, lu)
    return entity_learning_unit_yr_list


def _changed_in_period(start_date, end_date, changed_date):
    return convert_date_to_datetime(start_date) <= changed_date <= convert_date_to_datetime(end_date)
