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
from django.test import TestCase
from django.utils import timezone
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models import proposal_learning_unit
from base.models.enums import proposal_state, proposal_type
from base.models.enums import entity_container_year_link_type


class TestSearch(TestCase):
    def setUp(self):
        self.proposal_learning_unit = ProposalLearningUnitFactory()

    def test_find_by_learning_unit_year(self):
        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(
            self.proposal_learning_unit.learning_unit_year
        )
        self.assertEqual(a_proposal_learning_unit, self.proposal_learning_unit)

    def test_find_by_learning_unit(self):
        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit(
            self.proposal_learning_unit.learning_unit_year.learning_unit
        )
        self.assertEqual(a_proposal_learning_unit, self.proposal_learning_unit)

    def test_str(self):
        expected_str = "{} - {}".format(self.proposal_learning_unit.folder_id,
                                        self.proposal_learning_unit.learning_unit_year)
        self.assertEqual(str(self.proposal_learning_unit), expected_str)


class TestSearchCases(TestCase):

    def setUp(self):
        yr = timezone.now().year
        self.entity_1 = EntityFactory()
        entity_version_1 = EntityVersionFactory(entity=self.entity_1)
        self.an_academic_year = AcademicYearFactory(year=yr)
        self.an_acronym = "LBIO1212"

        self.learning_container_yr = LearningContainerYearFactory(academic_year=self.an_academic_year)
        entity_version_container_ye = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                                 entity=self.entity_1,
                                                                 type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        a_learning_unit_year = LearningUnitYearFactory(acronym=self.an_acronym,
                                                       academic_year=self.an_academic_year,
                                                       learning_container_year=self.learning_container_yr)
        self.a_proposal_learning_unit = ProposalLearningUnitFactory(learning_unit_year=a_learning_unit_year,
                                                                    type=proposal_type.ProposalType.CREATION,
                                                                    state=proposal_state.ProposalState.CENTRAL,
                                                                    entity=self.entity_1)

    def test_search_by_academic_year(self):
        results = proposal_learning_unit.search(academic_year_id=self.an_academic_year.id)
        self.check_search_result(results)

    def test_search_by_acronym(self):
        results = proposal_learning_unit.search(acronym=self.an_acronym)
        self.check_search_result(results)

        results = proposal_learning_unit.search(acronym=self.an_acronym[2:])
        self.check_search_result(results)

    def test_search_by_proposal_type(self):
        results = proposal_learning_unit.search(proposal_type=self.a_proposal_learning_unit.type)
        self.check_search_result(results)

    def test_search_by_proposal_state(self):
        results = proposal_learning_unit.search(proposal_state=self.a_proposal_learning_unit.state)
        self.check_search_result(results)

    def test_search_by_folder_id(self):
        results = proposal_learning_unit.search(folder_id=self.a_proposal_learning_unit.folder_id)
        self.check_search_result(results)

    def test_search_by_entity_folder(self):
        results = proposal_learning_unit.search(entity_folder_id=self.a_proposal_learning_unit.entity.id)
        self.check_search_result(results)

    def test_search_by_proposal_learning_container_yr(self):
        results = proposal_learning_unit.search(learning_container_year_id=self.learning_container_yr.id)
        self.check_search_result(results)

    def test_search_by_proposal_list_learning_container_yr(self):
        self.check_search_result(proposal_learning_unit.search(learning_container_year_id=[self.learning_container_yr.id]))

    def check_search_result(self, results):
        self.assertCountEqual(results, [self.a_proposal_learning_unit])

    def test_find_distinct_folder_entities(self):
        entity_2 = EntityFactory()
        ProposalLearningUnitFactory(entity=entity_2)

        entities_result = proposal_learning_unit.find_distinct_folder_entities()
        self.assertCountEqual(entities_result, [self.entity_1, entity_2])
