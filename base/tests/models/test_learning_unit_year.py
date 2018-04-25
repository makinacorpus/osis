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
from django.test import TestCase
from django.utils import timezone
from attribution.models import attribution

from base.models import learning_unit_year
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit_year import find_max_credits_of_related_partims
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, create_learning_units_year
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory


class LearningUnitYearTest(TestCase):
    def setUp(self):
        self.tutor = TutorFactory()
        self.academic_year = AcademicYearFactory(year=timezone.now().year)
        self.learning_unit_year = LearningUnitYearFactory(acronym="LDROI1004",
                                                          specific_title="Juridic law courses",
                                                          academic_year=self.academic_year,
                                                          subtype=learning_unit_year_subtypes.FULL)

    def test_find_by_tutor_with_none_argument(self):
        self.assertEqual(attribution.find_by_tutor(None), None)

    def test_subdivision_computation(self):
        l_container_year = LearningContainerYearFactory(acronym="LBIR1212", academic_year=self.academic_year)
        l_unit_1 = LearningUnitYearFactory(acronym="LBIR1212", learning_container_year=l_container_year,
                                           academic_year=self.academic_year)
        l_unit_2 = LearningUnitYearFactory(acronym="LBIR1212A", learning_container_year=l_container_year,
                                           academic_year=self.academic_year)
        l_unit_3 = LearningUnitYearFactory(acronym="LBIR1212B", learning_container_year=l_container_year,
                                           academic_year=self.academic_year)

        self.assertFalse(l_unit_1.subdivision)
        self.assertEqual(l_unit_2.subdivision, 'A')
        self.assertEqual(l_unit_3.subdivision, 'B')

    def test_search_acronym_by_regex(self):
        regex_valid = '^LD.+1+'
        query_result_valid = learning_unit_year.search(acronym=regex_valid)
        self.assertEqual(len(query_result_valid), 1)
        self.assertEqual(self.learning_unit_year.acronym, query_result_valid[0].acronym)

    def test_property_in_charge(self):
        self.assertFalse(self.learning_unit_year.in_charge)

        a_container_year = LearningContainerYearFactory(acronym=self.learning_unit_year.acronym,
                                                        academic_year=self.academic_year)
        self.learning_unit_year.learning_container_year = a_container_year

        self.assertFalse(self.learning_unit_year.in_charge)

        a_container_year.in_charge = True

        self.assertTrue(self.learning_unit_year.in_charge)

    def test_find_gte_learning_units_year(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2007]

        result = list(selected_learning_unit_year.find_gte_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertListEqual(result, list(range(2007,2018)))

    def test_find_gte_learning_units_year_case_no_future(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2017]

        result = list(selected_learning_unit_year.find_gte_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertEqual(result, [2017])

    def test_find_gt_learning_unit_year(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2007]

        result = list(selected_learning_unit_year.find_gt_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertListEqual(result, list(range(2008, 2018)))

    def test_find_gt_learning_units_year_case_no_future(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2017]

        result = list(selected_learning_unit_year.find_gt_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertEqual(result, [])

    def test_get_learning_unit_parent(self):
        lunit_container_year = LearningContainerYearFactory(academic_year=self.academic_year, acronym='LBIR1230')
        luy_parent = LearningUnitYearFactory(academic_year=self.academic_year, acronym='LBIR1230',
                                             learning_container_year=lunit_container_year,
                                             subtype=learning_unit_year_subtypes.FULL)
        luy_partim = LearningUnitYearFactory(academic_year=self.academic_year, acronym='LBIR1230B',
                                             learning_container_year=lunit_container_year,
                                             subtype=learning_unit_year_subtypes.PARTIM)
        self.assertEqual(luy_partim.parent, luy_parent)

    def test_get_learning_unit_parent_without_parent(self):
        lunit_container_year = LearningContainerYearFactory(academic_year=self.academic_year, acronym='LBIR1230')
        luy_parent = LearningUnitYearFactory(academic_year=self.academic_year, acronym='LBIR1230',
                                             learning_container_year=lunit_container_year,
                                             subtype=learning_unit_year_subtypes.FULL)
        self.assertIsNone(luy_parent.parent)

    def test_search_by_title(self):
        common_part = "commun"
        a_common_title = "Titre {}".format(common_part)
        a_specific_title = "Specific title {}".format(common_part)
        lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_year,
                                                          common_title=a_common_title)
        luy = LearningUnitYearFactory(academic_year=self.academic_year,
                                      specific_title=a_specific_title,
                                      learning_container_year=lunit_container_yr)


        self.assertEqual(learning_unit_year.search(title="{} en plus".format(a_common_title)).count(), 0)
        self.assertEqual(learning_unit_year.search(title=a_common_title)[0], luy)
        self.assertEqual(learning_unit_year.search(title=common_part)[0], luy)
        self.assertEqual(learning_unit_year.search(title=a_specific_title)[0], luy)


    def test_find_max_credits_of_partims(self):
        self.partim_1 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                learning_container_year=self.learning_unit_year.learning_container_year,
                                                subtype=learning_unit_year_subtypes.PARTIM, credits=15)
        self.partim_2 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                learning_container_year=self.learning_unit_year.learning_container_year,
                                                subtype=learning_unit_year_subtypes.PARTIM, credits=20)
        max_credits = find_max_credits_of_related_partims(self.learning_unit_year)
        self.assertEqual(max_credits, 20)

    def test_find_max_credits_of_partims_when_no_partims_related(self):
        max_credits = find_max_credits_of_related_partims(self.learning_unit_year)
        self.assertEqual(max_credits, None)

    def test_ccomplete_title_when_no_learning_container_year(self):
        specific_title = 'part 1: Vertebrate'

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year=None)
        self.assertEqual(luy.complete_title, specific_title)

    def test_complete_title_property_case_common_title_is_empty(self):
        specific_title = 'part 1: Vertebrate'

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year__common_title="")
        self.assertEqual(luy.complete_title, specific_title)

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year__common_title=None)
        self.assertEqual(luy.complete_title, specific_title)

    def test_complete_title_property_case_common_and_specific_title_are_set(self):
        specific_title = 'part 1: Vertebrate'
        common_title = 'Zoology'

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year__common_title=common_title)
        self.assertEqual(luy.complete_title, '{} {}'.format(common_title, specific_title))

    def test_common_title_property(self):
        self.assertEqual(self.learning_unit_year.container_common_title,
                         self.learning_unit_year.learning_container_year.common_title)

    def test_common_title_property_no_container(self):
        self.learning_unit_year.learning_container_year = None
        self.assertEqual(self.learning_unit_year.container_common_title, '')
