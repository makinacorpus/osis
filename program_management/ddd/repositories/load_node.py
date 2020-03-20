##############################################################################
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
##############################################################################
from typing import List

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Value, Case, When, IntegerField, CharField, QuerySet, Q

from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import AllTypes, EducationGroupTypesEnum
from base.models.group_element_year import GroupElementYear
from learning_unit.ddd.repository import load_learning_unit_year
from program_management.ddd.domain import node
from program_management.models.enums.node_type import NodeType

from learning_unit.ddd.business_types import *


def load_by_type(type: NodeType, element_id: int) -> node.Node:
    if type == NodeType.EDUCATION_GROUP:
        return load_node_education_group_year(element_id)
    elif type == NodeType.LEARNING_UNIT:
        return load_node_learning_unit_year(element_id)


def load_node_education_group_year(node_id: int) -> node.Node:
    try:
        node_data = __load_multiple_node_education_group_year([node_id])[0]
        return node.factory.get_node(**__convert_string_to_enum(node_data))
    except IndexError:
        raise node.NodeNotFoundException


def load_node_learning_unit_year(node_id: int) -> node.Node:
    try:
        node_data = __load_multiple_node_learning_unit_year([node_id])[0]
        return node.factory.get_node(**__convert_string_to_enum(node_data))
    except IndexError:
        raise node.NodeNotFoundException


# TODO :: create a new app group/ddd and move the fetch of Group, GroupYear into this new app? (like learning_unit?)
def load_multiple(element_ids: List[int]) -> List[node.Node]:
    qs = GroupElementYear.objects.filter(
        pk__in=element_ids
    ).filter(
        Q(child_leaf__isnull=False) | Q(child_branch__isnull=False)
    ).annotate(
        group_year_id=F('child_branch__pk'),
        learning_unit_year_id=F('child_leaf__pk'),
    ).values(
        'child_branch__pk',
        'learning_unit_year_id',
    )

    nodes_data = list(qs)

    learning_unit_pks = list(
        node_data['learning_unit_year_id'] for node_data in nodes_data
        if node_data['learning_unit_year_id']
    )

    group_pks = list(
        node_data['child_branch__pk'] for node_data in nodes_data
        if node_data['child_branch__pk']
    )

    nodes_objects = [node.factory.get_node(**__convert_string_to_enum(node_data))
                     for node_data in __load_multiple_node_education_group_year(group_pks)]

    return nodes_objects + __load_multiple_node_learning_unit_year(learning_unit_pks)


def __convert_string_to_enum(node_data: dict) -> dict:
    if node_data.get('node_type'):
        node_data['node_type'] = __convert_node_type_enum(node_data['node_type'])
    node_data['type'] = NodeType[node_data['type']]
    return node_data


def __convert_node_type_enum(str_node_type: str) -> EducationGroupTypesEnum:
    enum_node_type = None
    for sub_enum in EducationGroupTypesEnum.__subclasses__():
        try:
            enum_node_type = sub_enum[str_node_type]
        except KeyError:
            pass
    if not enum_node_type:
        raise KeyError("Cannot convert '{}' str type to '{}' type".format(str_node_type, EducationGroupTypesEnum))
    return enum_node_type


def __load_multiple_node_education_group_year(node_group_year_ids: List[int]) -> QuerySet:
    return EducationGroupYear.objects.filter(pk__in=node_group_year_ids).annotate(
        node_id=F('pk'),
        type=Value(NodeType.EDUCATION_GROUP.name, output_field=CharField()),
        node_type=F('education_group_type__name'),
        code=F('partial_acronym'),
        title_t=F('acronym'),
        year=F('academic_year__year'),
        remark_fr=F('remark'),
        remark_en=F('remark_english'),

        # TODO :: Warning Should load this into education_group/ddd/repository (when model refactor to GroupYear)
        offer_partial_title_fr=F('partial_title'),
        offer_partial_title_en=F('partial_title_english'),
        offer_title_fr=F('title'),
        offer_title_en=F('title_english'),

    ).values(
        'node_id',
        'type',
        'node_type',
        'code',
        'title_t',
        'offer_title_fr',
        'offer_title_en',
        'year',
        'constraint_type',
        'min_constraint',
        'max_constraint',
        'remark_fr',
        'remark_en',
        'offer_partial_title_fr',
        'offer_partial_title_en',
        'credits',
    ).annotate(title=F('title_t')).values(
        'node_id',
        'type',
        'node_type',
        'code',
        'title',
        'offer_title_fr',
        'offer_title_en',
        'year',
        'constraint_type',
        'min_constraint',
        'max_constraint',
        'remark_fr',
        'remark_en',
        'offer_partial_title_fr',
        'offer_partial_title_en',
        'credits',
    )


def __load_multiple_node_learning_unit_year(node_learning_unit_year_ids: List[int]):
    nodes = []
    for lu in load_learning_unit_year.load_multiple(node_learning_unit_year_ids):
        node_data = {
            'node_id': lu.id,
            'type': NodeType.LEARNING_UNIT.name,
            'year': lu.year,
            'proposal_type': lu.proposal_type,
            'code': lu.acronym,
            'title': lu.full_title_fr,
            'credits': lu.credits,
            'status': lu.credits,
            'periodicity': lu.credits,
            'common_title_fr': lu.common_title_fr,
            'specific_title_fr': lu.specific_title_fr,
            'common_title_en': lu.common_title_en,
            'specific_title_en': lu.specific_title_en,
        }
        nodes.append(node.factory.get_node(**__convert_string_to_enum(node_data)))
    return nodes
