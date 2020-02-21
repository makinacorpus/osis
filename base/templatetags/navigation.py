############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
import urllib

from django.http import QueryDict
from django.template.defaulttags import register
from django.urls import reverse

from base.forms.education_groups import EducationGroupFilter
from base.forms.learning_unit.search.borrowed import BorrowedLearningUnitSearch
from base.forms.learning_unit.search.educational_information import LearningUnitDescriptionFicheFilter
from base.forms.learning_unit.search.external import ExternalLearningUnitFilter
from base.forms.learning_unit.search.service_course import ServiceCourseFilter
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.forms.proposal.learning_unit_proposal import ProposalLearningUnitFilter
from base.models.education_group_year import EducationGroupYear
from base.views.learning_units.search.common import SearchTypes


@register.inclusion_tag('templatetags/navigation.html', takes_context=False)
def navigation(get_parameters: QueryDict, element, url_name: str):
    context = {"current_element": element}
    if "search_query" not in get_parameters and "index" not in get_parameters:
        return context

    search_query_string = get_parameters.get("search_query")
    index = int(get_parameters.get("index"))
    search_type = get_parameters.get("search_type")

    unquoted_search_query_string = urllib.parse.unquote_plus(search_query_string)
    search_parameters = QueryDict(unquoted_search_query_string).dict()

    if isinstance(element, EducationGroupYear):
        filter_form_class = EducationGroupFilter
        reverse_url_function = _reverse_education_group_year_url
    else:
        filter_form_class = _get_learning_unit_forms(search_type)
        reverse_url_function = _reverse_learning_unit_year_url

    qs = filter_form_class(data=search_parameters).qs
    next_element = _get_element(qs, index + 1)
    next_element_get_parameters = get_parameters.copy()
    next_element_get_parameters["index"] = index + 1

    previous_element = _get_element(qs, index - 1)
    previous_element_get_parameters = get_parameters.copy()
    previous_element_get_parameters["index"] = index - 1

    context.update({
        "next_element": next_element,
        "next_url": reverse_url_function(next_element, url_name, next_element_get_parameters)
        if next_element else None,
        "previous_element": previous_element,
        "previous_url": reverse_url_function(previous_element, url_name, previous_element_get_parameters)
        if previous_element else None
    })
    return context


def _get_learning_unit_forms(search_type):
    map_search_type_to_filter_form = {
        SearchTypes.SIMPLE_SEARCH.value: LearningUnitFilter,
        SearchTypes.SERVICE_COURSES_SEARCH.value: ServiceCourseFilter,
        SearchTypes.PROPOSAL_SEARCH.value: ProposalLearningUnitFilter,
        SearchTypes.SUMMARY_LIST.value: LearningUnitDescriptionFicheFilter,
        SearchTypes.BORROWED_COURSE.value: BorrowedLearningUnitSearch,
        SearchTypes.EXTERNAL_SEARCH.value: ExternalLearningUnitFilter,
    }
    return map_search_type_to_filter_form.get(int(search_type) if search_type else None, LearningUnitFilter)


def _get_element(qs, index):
    try:
        return qs[index] if index >= 0 else None
    except IndexError:
        return None


def _reverse_education_group_year_url(education_group_year_obj, url_name, get_parameters):
    return "{}?{}".format(
        reverse(url_name, args=[education_group_year_obj.id, education_group_year_obj.id]),
        get_parameters.urlencode()
    )


def _reverse_learning_unit_year_url(learning_unit_year_obj, url_name, get_parameters: QueryDict):
    return "{}?{}".format(
        reverse(url_name, args=[learning_unit_year_obj.id]),
        get_parameters.urlencode()
    )
