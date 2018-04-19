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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import mock
from base.models.enums import education_group_categories
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from django.test import TestCase
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.models import group_element_year


class GroupElementYearTest(TestCase):

    def test_find_by_parent(self):
        academic_year = AcademicYearFactory()

        education_group_year_parent = EducationGroupYearFactory(academic_year=academic_year)

        education_group_branch_1 = EducationGroupYearFactory(academic_year=academic_year)
        education_group_brancg_2 = EducationGroupYearFactory(academic_year=academic_year)

        group_element_year_1 = GroupElementYearFactory(parent=education_group_year_parent,
                                                       child_branch=education_group_branch_1)
        group_element_year_2 = GroupElementYearFactory(parent=education_group_year_parent,
                                                       child_branch=education_group_brancg_2)

        self.assertCountEqual(group_element_year.find_by_parent(education_group_year_parent), [group_element_year_1, group_element_year_2])


class TestFindBuildParentListByEducationGroupYearId(TestCase):
    """Unit tests for _build_parent_list_by_education_group_year_id() function"""
    def setUp(self):
        current_academic_year = create_current_academic_year()
        root_group_type = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)
        self.root = EducationGroupYearFactory(academic_year=current_academic_year, education_group_type=root_group_type)

        group_type = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        self.child_branch = EducationGroupYearFactory(academic_year=current_academic_year, education_group_type=group_type)
        GroupElementYearFactory(parent=self.root, child_branch=self.child_branch)

        self.child_leaf = LearningUnitYearFactory(academic_year=current_academic_year)
        GroupElementYearFactory(parent=self.child_branch, child_branch=None, child_leaf=self.child_leaf)

    def test_with_filters(self):
        self.maxDiff = None
        filters = {
            'parent__education_group_type__category': [education_group_categories.TRAINING]
        }
        result = group_element_year._build_parent_list_by_education_group_year_id(self.child_leaf.academic_year, filters=filters)

        expected_result = {
            'child_branch_{}'.format(self.child_branch.id): [{
                'parent': self.root.id,
                'child_branch': self.child_branch.id,
                'child_leaf': None,
                'parent__education_group_type__category': self.root.education_group_type.category
            },],
            'child_leaf_{}'.format(self.child_leaf.id): [{
                'parent': self.child_branch.id,
                'child_branch': None,
                'child_leaf': self.child_leaf.id,
                'parent__education_group_type__category': self.child_branch.education_group_type.category
            },]
        }
        self.assertEqual(len(result), len(expected_result))
        self.assertDictEqual(result, expected_result)

    def test_without_filters(self):
        result = group_element_year._build_parent_list_by_education_group_year_id(self.child_leaf.academic_year)
        expected_result = {
            'child_branch_{}'.format(self.child_branch.id): [{
                'parent': self.root.id,
                'child_branch': self.child_branch.id,
                'child_leaf': None,
            },],
            'child_leaf_{}'.format(self.child_leaf.id): [{
                'parent': self.child_branch.id,
                'child_branch': None,
                'child_leaf': self.child_leaf.id,
            },]
        }
        self.assertEqual(len(result), len(expected_result))
        self.assertDictEqual(result, expected_result)


class TestFindRelatedRootEducationGroups(TestCase):
    """Unit tests for _find_related_root_education_groups() function"""
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.child_leaf = LearningUnitYearFactory(academic_year=self.current_academic_year)

        root_group_type = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)
        self.root = EducationGroupYearFactory(academic_year=self.current_academic_year, education_group_type=root_group_type)

    @mock.patch('base.models.group_element_year._raise_if_incorrect_instance')
    def test_objects_instances_check_is_called(self, mock_check_instance):
        group_element_year._find_related_root_education_groups([self.child_leaf])
        self.assertTrue(mock_check_instance.called)

    def test_without_filters_case_direct_parent_id_root(self):
        element_year = GroupElementYearFactory(parent=self.root, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year._find_related_root_education_groups([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [element_year.parent.id]
        }
        self.assertEqual(result, expected_result)

    def test_without_filters_case_parent_in_2nd_level(self):
        child_branch = EducationGroupYearFactory(academic_year=self.current_academic_year)
        element_year = GroupElementYearFactory(parent=self.root, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year._find_related_root_education_groups([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [element_year.parent.id]
        }
        self.assertDictEqual(result, expected_result)

    def test_without_filters_case_multiple_parents_in_2nd_level(self):
        root_2 = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(name='Master', category=education_group_categories.TRAINING)
        )
        child_branch = EducationGroupYearFactory(academic_year=self.current_academic_year)
        GroupElementYearFactory(parent=self.root, child_branch=child_branch)
        GroupElementYearFactory(parent=root_2, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year._find_related_root_education_groups([self.child_leaf])
        expected_result = {
            self.child_leaf.id: [self.root.id, root_2.id]
        }
        self.assertEqual(len(result[self.child_leaf.id]), 2)
        self.assertIn(self.root.id, result[self.child_leaf.id])
        self.assertIn(root_2.id, result[self.child_leaf.id])

    def test_without_filters_case_direct_parent_academic_year_is_different(self):
        current_academic_year = create_current_academic_year()
        root_group_type = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)
        self.root = EducationGroupYearFactory(academic_year=current_academic_year, education_group_type=root_group_type)
        child_branch = EducationGroupYearFactory(
            academic_year=AcademicYearFactory(year=current_academic_year.year - 1)
        )
        GroupElementYearFactory(parent=self.root, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        result = group_element_year._find_related_root_education_groups([self.child_leaf])
        self.assertEqual(result[self.child_leaf.id], [self.root.id])

    def test_without_filters_case_childs_with_different_academic_years(self):
        child_leaf_other_ac_year = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=self.current_academic_year.year - 1)
        )
        with self.assertRaises(AttributeError):
            group_element_year._find_related_root_education_groups([self.child_leaf, child_leaf_other_ac_year])

    def test_with_filters_case_direct_parent_is_root_and_not_matches_filter(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(name='Options choices', category=education_group_categories.GROUP)
        )
        GroupElementYearFactory(parent=root, child_branch=None, child_leaf=self.child_leaf)
        filters = {
            'parent__education_group_type__category': [education_group_categories.TRAINING]
        }
        expected_result = {
            self.child_leaf.id: [root.id]
        }
        result = group_element_year._find_related_root_education_groups([self.child_leaf], filters=filters)
        self.assertDictEqual(result, expected_result)

    def test_with_filters_case_root_in_2nd_level_anddirect_parent_matches_filter(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(name='Master', category=education_group_categories.TRAINING)
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
            education_group_type=EducationGroupTypeFactory(name='Didactic Master', category=education_group_categories.TRAINING)
        )
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        GroupElementYearFactory(parent=child_branch, child_branch=None, child_leaf=self.child_leaf)
        filters = {
            'parent__education_group_type__category': [education_group_categories.TRAINING]
        }
        result = group_element_year._find_related_root_education_groups([self.child_leaf], filters=filters)
        expected_result = {
            self.child_leaf.id: [child_branch.id]
        }
        self.assertDictEqual(result, expected_result)
        self.assertNotIn(root.id, result)

    def test_without_filters_case_objects_are_education_group_instance(self):
        root = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
        )
        child_branch = EducationGroupYearFactory(
            academic_year=self.current_academic_year,
        )
        GroupElementYearFactory(parent=root, child_branch=child_branch)
        result = group_element_year._find_related_root_education_groups([child_branch])
        expected_result = {
            child_branch.id: [root.id]
        }
        self.assertDictEqual(result, expected_result)


class TestFindLearningUnitFormationRoots(TestCase):
    """Unit tests for find_learning_unit_formation_roots()"""
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.child_leaf = LearningUnitYearFactory(academic_year=self.current_academic_year)

    def _build_hierarchy(self, academic_year, direct_parent_type, child_leaf):
        group_element_child = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=academic_year, education_group_type=direct_parent_type),
            child_branch=None,
            child_leaf=child_leaf
        )
        group_element_root = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=academic_year),
            child_branch=group_element_child.parent,
        )
        return locals()

    def test_group_type_option_is_correctly_excluded(self):
        type_option = EducationGroupTypeFactory(name='Option', category=education_group_categories.MINI_TRAINING)
        hierarchy = self._build_hierarchy(self.current_academic_year, type_option, self.child_leaf)
        result = group_element_year.find_learning_unit_formation_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])

    def test_all_group_types_of_category_mini_training_stops_recursivity(self):
        group_type = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        hierarchy = self._build_hierarchy(self.current_academic_year, group_type, self.child_leaf)
        result = group_element_year.find_learning_unit_formation_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])

    def test_all_group_types_of_category_training_stops_recursivity(self):
        type_bachelor = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)
        hierarchy = self._build_hierarchy(self.current_academic_year, type_bachelor, self.child_leaf)
        result = group_element_year.find_learning_unit_formation_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])

    def test_case_group_category_is_not_root(self):
        a_group_type = EducationGroupTypeFactory(name='Subgroup', category=education_group_categories.GROUP)
        hierarchy = self._build_hierarchy(self.current_academic_year, a_group_type, self.child_leaf)
        result = group_element_year.find_learning_unit_formation_roots([self.child_leaf])
        self.assertNotIn(hierarchy['group_element_child'].parent.id, result[self.child_leaf.id])
        self.assertIn(hierarchy['group_element_root'].parent.id, result[self.child_leaf.id])

    def test_case_group_category_is_root(self):
        a_group_type = EducationGroupTypeFactory(name='Subgroup', category=education_group_categories.GROUP)
        group_element = GroupElementYearFactory(
            parent=EducationGroupYearFactory(academic_year=self.current_academic_year, education_group_type=a_group_type),
            child_branch=None,
            child_leaf=self.child_leaf
        )
        result = group_element_year.find_learning_unit_formation_roots([self.child_leaf])
        self.assertEqual(result[self.child_leaf.id], [group_element.parent.id])

    def test_case_arg_is_empty(self):
        result = group_element_year.find_learning_unit_formation_roots([])
        self.assertEqual(result, {})

    def test_case_arg_is_none(self):
        result = group_element_year.find_learning_unit_formation_roots(None)
        self.assertEqual(result, {})


class TestBuildChildKey(TestCase):
    """Unit tests on _build_child_key() """
    def test_case_params_are_none(self):
        with self.assertRaises(AttributeError):
            group_element_year._build_child_key()

    def test_case_two_params_are_set(self):
        with self.assertRaises(AttributeError):
            group_element_year._build_child_key(child_branch=1234, child_leaf=5678)

    def test_case_child_branch_is_set(self):
        result = group_element_year._build_child_key(child_branch=5678)
        self.assertEqual(result, 'child_branch_5678')

    def test_case_child_leaf_is_set(self):
        result = group_element_year._build_child_key(child_leaf=5678)
        self.assertEqual(result, 'child_leaf_5678')


class TestRaiseIfIncorrectInstance(TestCase):
    def test_case_unothorized_instance(self):
        with self.assertRaises(AttributeError):
            group_element_year._raise_if_incorrect_instance([AcademicYearFactory()])

    def test_case_different_objects_instances(self):
        with self.assertRaises(AttributeError):
            group_element_year._raise_if_incorrect_instance([EducationGroupYearFactory(), LearningUnitYearFactory()])
