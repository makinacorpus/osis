##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums import prerequisite_operator, education_group_categories
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from education_group.api.serializers.prerequisite import EducationGroupPrerequisitesSerializerLearningUnit
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TrainingPrerequisitesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        root_node
        |-----common_core
             |---- LDROI100A (UE)
        |----subgroup1
             |---- LDROI120B (UE)
             |----subgroup2
                  |---- LDROI100A (UE)
        :return:
        """
        cls.person = PersonFactory()
        cls.root_node = NodeGroupYearFactory(node_id=1, code="LBIR100B", title="Bachelier en droit", year=2018)
        cls.common_core = NodeGroupYearFactory(node_id=2, code="LGROUP100A", title="Tronc commun", year=2018)
        cls.ldroi100a = NodeLearningUnitYearFactory(node_id=3, code="LDROI100A", title="Introduction", year=2018)
        cls.ldroi120b = NodeLearningUnitYearFactory(node_id=4, code="LDROI120B", title="Séminaire", year=2018)
        cls.subgroup1 = NodeGroupYearFactory(node_id=5, code="LSUBGR100G", title="Sous-groupe 1", year=2018)
        cls.subgroup2 = NodeGroupYearFactory(node_id=6, code="LSUBGR150G", title="Sous-groupe 2", year=2018)

        cls.ldroi1300 = NodeLearningUnitYearFactory(node_id=7, code="LDROI1300", title="Introduction droit", year=2018)
        cls.lagro2400 = NodeLearningUnitYearFactory(node_id=8, code="LAGRO2400", title="Séminaire agro", year=2018)

        cls.root_egy = EducationGroupYearFactory(id=cls.root_node.node_id,
                                                 education_group_type__category=education_group_categories.TRAINING,
                                                 acronym=cls.root_node.code,
                                                 title=cls.root_node.title,
                                                 academic_year__year=cls.root_node.year)

        LinkFactory(parent=cls.root_node, child=cls.common_core)
        LinkFactory(parent=cls.common_core, child=cls.ldroi100a)
        LinkFactory(parent=cls.root_node, child=cls.subgroup1)
        LinkFactory(parent=cls.subgroup1, child=cls.ldroi120b)
        LinkFactory(parent=cls.subgroup1, child=cls.subgroup2)
        LinkFactory(parent=cls.subgroup2, child=cls.ldroi100a)

        cls.p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.AND)
        cls.p_group.add_prerequisite_item('LDROI1300', 2018)
        cls.p_group.add_prerequisite_item('LAGRO2400', 2018)

        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        p_req.add_prerequisite_item_group(cls.p_group)
        cls.ldroi100a.set_prerequisite(p_req)

        cls.tree = ProgramTree(root_node=cls.root_node)

        cls.url = reverse('education_group_api_v1:training-prerequisites', kwargs={'year': cls.root_node.year,
                                                                                   'acronym': cls.root_node.code})
        cls.request = RequestFactory().get(cls.url)
        cls.serializer = EducationGroupPrerequisitesSerializerLearningUnit(cls.ldroi100a, context={
            'request': cls.request,
            'language': settings.LANGUAGE_CODE_EN,
            'tree': cls.tree
        })

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            with self.subTest(method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results_case_education_group_year_not_found(self):
        invalid_url = reverse('education_group_api_v1:training-prerequisites', kwargs={
            'acronym': 'ACRO',
            'year': 2019
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('education_group.api.views.prerequisite.TrainingPrerequisites.get_queryset')
    def test_get_results(self, mock_get_queryset):
        mock_get_queryset.return_value = self.tree.get_nodes_that_have_prerequisites()
        response = self.client.get(self.url)
        with self.subTest('Test status code'):
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest('Test response'):
            self.assertEqual([self.serializer.data], response.json())


class MiniTrainingPrerequisitesTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        root_node
        |-----common_core
             |---- LDROI100A (UE)
        |----subgroup1
             |---- LDROI120B (UE)
             |----subgroup2
                  |---- LDROI100A (UE)
        :return:
        """
        cls.person = PersonFactory()
        cls.root_node = NodeGroupYearFactory(node_id=1, code="LBIR100B", title="Bachelier en droit", year=2018)
        cls.common_core = NodeGroupYearFactory(node_id=2, code="LGROUP100A", title="Tronc commun", year=2018)
        cls.ldroi100a = NodeLearningUnitYearFactory(node_id=3, code="LDROI100A", title="Introduction", year=2018)
        cls.ldroi120b = NodeLearningUnitYearFactory(node_id=4, code="LDROI120B", title="Séminaire", year=2018)
        cls.subgroup1 = NodeGroupYearFactory(node_id=5, code="LSUBGR100G", title="Sous-groupe 1", year=2018)
        cls.subgroup2 = NodeGroupYearFactory(node_id=6, code="LSUBGR150G", title="Sous-groupe 2", year=2018)

        cls.ldroi1300 = NodeLearningUnitYearFactory(node_id=7, code="LDROI1300", title="Introduction droit", year=2018)
        cls.lagro2400 = NodeLearningUnitYearFactory(node_id=8, code="LAGRO2400", title="Séminaire agro", year=2018)

        cls.root_egy = EducationGroupYearFactory(id=cls.root_node.node_id,
                                                 education_group_type__category=
                                                 education_group_categories.MINI_TRAINING,
                                                 partial_acronym=cls.root_node.code,
                                                 title=cls.root_node.title,
                                                 academic_year__year=cls.root_node.year)

        LinkFactory(parent=cls.root_node, child=cls.common_core)
        LinkFactory(parent=cls.common_core, child=cls.ldroi100a)
        LinkFactory(parent=cls.root_node, child=cls.subgroup1)
        LinkFactory(parent=cls.subgroup1, child=cls.ldroi120b)
        LinkFactory(parent=cls.subgroup1, child=cls.subgroup2)
        LinkFactory(parent=cls.subgroup2, child=cls.ldroi100a)

        cls.p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.AND)
        cls.p_group.add_prerequisite_item('LDROI1300', 2018)
        cls.p_group.add_prerequisite_item('LAGRO2400', 2018)

        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        p_req.add_prerequisite_item_group(cls.p_group)
        cls.ldroi100a.set_prerequisite(p_req)

        cls.tree = ProgramTree(root_node=cls.root_node)

        cls.url = reverse('education_group_api_v1:mini_training-prerequisites', kwargs={'year': cls.root_node.year,
                                                                                        'partial_acronym':
                                                                                            cls.root_node.code})
        cls.request = RequestFactory().get(cls.url)
        cls.serializer = EducationGroupPrerequisitesSerializerLearningUnit(cls.ldroi100a, context={
            'request': cls.request,
            'language': settings.LANGUAGE_CODE_EN,
            'tree': cls.tree
        })

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            with self.subTest(method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results_case_education_group_year_not_found(self):
        invalid_url = reverse('education_group_api_v1:mini_training-prerequisites', kwargs={
            'partial_acronym': 'ACRO',
            'year': 2019
        })
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('education_group.api.views.prerequisite.MiniTrainingPrerequisites.get_queryset')
    def test_get_results(self, mock_get_queryset):
        mock_get_queryset.return_value = self.tree.get_nodes_that_have_prerequisites()
        response = self.client.get(self.url)
        with self.subTest('Test status code'):
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest('Test response'):
            self.assertEqual([self.serializer.data], response.json())

