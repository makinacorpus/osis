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
from base.models.education_group_type import GROUP_TYPE_OPTION
from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from django.db import models
from django.contrib import admin
from base.models.enums import sessions_derogation
from base.models.enums import education_group_categories
from base.models import education_group_type
from django.db.models import Q


class GroupElementYearAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child_branch', 'child_leaf',)
    fieldsets = ((None, {'fields': ('parent', 'child_branch', 'child_leaf', 'relative_credits',
                                    'min_credits', 'max_credits', 'is_mandatory', 'block', 'current_order',
                                    'own_comment', 'sessions_derogation', 'minor_access', 'comment',
                                    'comment_english',)}),)
    search_fields = ['child_branch__acronym', 'child_branch__partial_acronym', 'child_leaf__acronym', 'parent__acronym',
                     'parent__partial_acronym']
    raw_id_fields = ('parent', 'child_branch', 'child_leaf',)
    list_filter = ('is_mandatory', 'minor_access', 'sessions_derogation')


class GroupElementYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    parent = models.ForeignKey('EducationGroupYear', related_name='parent', blank=True, null=True)
    child_branch = models.ForeignKey('EducationGroupYear', related_name='child_branch', blank=True, null=True)
    child_leaf = models.ForeignKey('LearningUnitYear', related_name='child_leaf', blank=True, null=True)
    relative_credits = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    min_credits = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    max_credits = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    is_mandatory = models.BooleanField(default=False)
    block = models.CharField(max_length=7, blank=True, null=True)
    current_order = models.IntegerField(blank=True, null=True)
    minor_access = models.BooleanField(default=False)
    comment = models.CharField(max_length=500, blank=True, null=True)
    comment_english = models.CharField(max_length=500, blank=True, null=True)
    own_comment = models.CharField(max_length=500, blank=True, null=True)
    sessions_derogation = models.CharField(max_length=65,
                                           choices=sessions_derogation.SessionsDerogationTypes.choices(),
                                           default=sessions_derogation.SessionsDerogationTypes.SESSION_UNDEFINED.value)


def search(**kwargs):
    queryset = GroupElementYear.objects

    if 'academic_year' in kwargs:
        academic_year = kwargs['academic_year']
        queryset = queryset.filter(Q(parent__academic_year=academic_year) |
                                   Q(child_branch__academic_year=academic_year) |
                                   Q(child_leaf__academic_year=academic_year))

    if 'child_leaf' in kwargs:
        queryset = queryset.filter(child_leaf=kwargs['child_leaf'])

    return queryset


def find_by_parent(an_education_group_year):
    return GroupElementYear.objects.filter(parent=an_education_group_year)


def find_learning_unit_formation_roots(objects):
    if objects:
        filters = _get_root_filters()
        return _find_related_root_education_groups(objects, filters=filters)
    return {}


def _get_root_filters():
    root_type_names = education_group_type.search(category=education_group_categories.MINI_TRAINING) \
        .exclude(name=GROUP_TYPE_OPTION).values_list('name', flat=True)
    root_categories = [education_group_categories.TRAINING]
    return {
        'parent__education_group_type__name': root_type_names,
        'parent__education_group_type__category': root_categories
    }


def _raise_if_incorrect_instance(objects):
    first_obj = objects[0]
    obj_class = first_obj.__class__
    if obj_class not in [LearningUnitYear, EducationGroupYear]:
        raise AttributeError("Objects must be either LearningUnitYear or EducationGroupYear intances.")
    if any(obj for obj in objects if obj.__class__ != obj_class):
        raise AttributeError("All objects must be the same class instance ({})".format(obj_class))


def _find_related_root_education_groups(objects, filters=None):
    _raise_if_incorrect_instance(objects)
    academic_year = _extract_common_academic_year(objects)
    parents_by_id = _build_parent_list_by_education_group_year_id(academic_year, filters=filters)
    if isinstance(objects[0], LearningUnitYear):
        return {obj.id: _find_elements(parents_by_id, child_leaf_id=obj.id, filters=filters) for obj in objects}
    else:
        return {obj.id: _find_elements(parents_by_id, child_branch_id=obj.id, filters=filters) for obj in objects}


def _extract_common_academic_year(objects):
    if len(set(getattr(obj, 'academic_year_id') for obj in objects)) > 1:
        raise AttributeError("The algorithm should load only graph/structure for 1 academic_year "
                             "to avoid too large 'in-memory' data.")
    return objects[0].academic_year


def _build_parent_list_by_education_group_year_id(academic_year, filters=None):
    columns_needed_for_filters = filters.keys() if filters else []
    group_elements = list(search(academic_year=academic_year)
                          .filter(parent__isnull=False)
                          .filter(Q(child_leaf__isnull=False) | Q(child_branch__isnull=False))
                          .select_related('education_group_year__education_group_type')
                          .values('parent', 'child_branch', 'child_leaf', *columns_needed_for_filters))
    result = {}
    # TODO :: uses .annotate() on queryset to make the below expected result
    for group_element_year in group_elements:
        key = _build_child_key(child_branch=group_element_year['child_branch'],
                               child_leaf=group_element_year['child_leaf'])
        result.setdefault(key, []).append(group_element_year)
    return result


def _build_child_key(child_branch=None, child_leaf=None):
    args = [child_leaf, child_branch]
    if not any(args) or all(args):
        raise AttributeError('Only one of the 2 param must bet set (not both of them).')
    if child_leaf:
        branch_part = 'child_leaf'
        id_part = child_leaf
    else:
        branch_part = 'child_branch'
        id_part = child_branch
    return '{branch_part}_{id_part}'.format(**locals())


def _find_elements(group_elements_by_child_id, child_leaf_id=None, child_branch_id=None, filters=None):
    roots = []
    unique_child_key = _build_child_key(child_leaf=child_leaf_id, child_branch=child_branch_id)
    group_elem_year_parents = group_elements_by_child_id.get(unique_child_key)
    # if has no parent
    if not group_elem_year_parents:
        # Must be 2 separated 'if' statements ; in case child_branch_id is not set but the child_leaf_id is set,
        # it means that the child_leaf has any parent. The function will return [].
        if child_branch_id:
            roots.append(child_branch_id)
    else:
        for group_elem_year in group_elem_year_parents:
            parent_id = group_elem_year['parent']
            if filters and _match_any_filters(group_elem_year, filters):
                # If record matches any filter, we must stop mounting across the hierarchy.
                roots.append(parent_id)
            else:
                # Recursive call ; the parent_id becomes the child_branch.
                roots.extend(_find_elements(group_elements_by_child_id, child_branch_id=parent_id, filters=filters))
    return roots


def _match_any_filters(element_year, filters):
    return any(element_year[col_name] in values_list for col_name, values_list in filters.items())
