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
from django.test import TestCase

from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, GroupType
from program_management.ddd.domain.authorized_relationship import AuthorizedRelationshipList
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory, \
    AuthorizedRelationshipFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestInit(TestCase):
    def test_normal_usage(self):
        auth_relations = AuthorizedRelationshipListFactory()
        result = AuthorizedRelationshipList(auth_relations)
        self.assertEqual(auth_relations, result.authorized_relationships)

    def test_when_authorized_relationships_arg_is_none(self):
        with self.assertRaises(AssertionError):
            AuthorizedRelationshipList(None)

    def test_when_authorized_relationships_arg_is_not_a_list(self):
        with self.assertRaises(AssertionError):
            AuthorizedRelationshipList("I'm not a list")

    def test_when_authorized_relationships_arg_is_empty(self):
        with self.assertRaises(AssertionError):
            AuthorizedRelationshipList([])

    def test_when_authorized_relationships_arg_is_wrong_instance(self):
        with self.assertRaises(AssertionError):
            wrong_instance = NodeGroupYearFactory()
            AuthorizedRelationshipList([wrong_instance])


class TestGetAuthorizedRelationship(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.auth_relation = AuthorizedRelationshipFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.COMMON_CORE
        )
        cls.auth_relations = AuthorizedRelationshipList([cls.auth_relation])
        cls.authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        cls.authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)

    def test_when_child_type_matches_but_not_parent_type(self):
        unauthorized_child = NodeGroupYearFactory(node_type=TrainingType.ACCESS_CONTEST)
        result = self.auth_relations._get_authorized_relationship(self.authorized_parent, unauthorized_child)
        self.assertIsNone(result)

    def test_when_parent_type_matches_but_not_parent_type(self):
        unauthorized_parent = NodeGroupYearFactory(node_type=TrainingType.INTERNSHIP)
        result = self.auth_relations._get_authorized_relationship(unauthorized_parent, self.authorized_child)
        self.assertIsNone(result)

    def test_when_parent_type_and_child_type_matches(self):
        parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        result = self.auth_relations._get_authorized_relationship(parent, child)
        self.assertEqual(self.auth_relation, result)


class TestIsAuthorized(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.auth_relation = AuthorizedRelationshipFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.COMMON_CORE
        )
        cls.auth_relations = AuthorizedRelationshipList([cls.auth_relation])

    def test_when_is_authorized(self):
        parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        result = self.auth_relations._get_authorized_relationship(parent, child)
        self.assertTrue(result)

    def test_when_is_not_authorized(self):
        parent = NodeGroupYearFactory(node_type=TrainingType.INTERNSHIP)
        child = NodeGroupYearFactory(node_type=GroupType.FINALITY_120_LIST_CHOICE)
        result = self.auth_relations._get_authorized_relationship(parent, child)
        self.assertFalse(result)


class TestGetAuthorizedChildrenTypes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.auth_relation = AuthorizedRelationshipFactory(
            parent_type=TrainingType.BACHELOR, child_type=GroupType.COMMON_CORE
        )
        cls.auth_relations = AuthorizedRelationshipList([cls.auth_relation])
        cls.authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        cls.authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)

    def test_result_is_a_set_instance(self):
        error_msg = """Useful for performance"""
        result = self.auth_relations.get_authorized_children_types(self.authorized_parent)
        self.assertIsInstance(result, set, error_msg)

    # def test_
