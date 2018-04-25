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
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from django.test import TestCase
from base.models.education_group_year import offer_year_entity_type, find_by_id, search, find_with_enrollments_count
from base.models.exceptions import MaximumOneParentAllowedException
from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_domain import OfferYearDomainFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory


class EducationGroupYearTest(TestCase):

    def setUp(self):

        academic_year = AcademicYearFactory()
        self.education_group_type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        self.education_group_type_minitraining = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        self.education_group_type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)

        self.education_group_year_1 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_training)
        self.education_group_year_2 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_minitraining)

        self.education_group_year_3 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_training)
        self.education_group_year_4 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_group)
        self.education_group_year_5 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_group)

        self.offer_year_2 = OfferYearFactory(academic_year=academic_year)
        self.offer_year_domain = OfferYearDomainFactory(offer_year=self.offer_year_2,
                                                        education_group_year=self.education_group_year_2)
        self.offer_year_entity_admin = OfferYearEntityFactory(offer_year=self.offer_year_2,
                                                              education_group_year=self.education_group_year_2,
                                                              type=offer_year_entity_type.ENTITY_ADMINISTRATION)
        self.entity_version_admin = EntityVersionFactory(entity=self.offer_year_entity_admin.entity,
                                                         parent=None)

        self.offer_year_3 = OfferYearFactory(academic_year=academic_year)
        self.offer_year_entity_management = OfferYearEntityFactory(offer_year=self.offer_year_3,
                                                                   education_group_year=self.education_group_year_3,
                                                                   type=offer_year_entity_type.ENTITY_MANAGEMENT)
        self.entity_version_management = EntityVersionFactory(entity=self.offer_year_entity_management.entity,
                                                         parent=None)

        self.group_element_year_4 = GroupElementYearFactory(parent=self.education_group_year_3,
                                                     child_branch=self.education_group_year_1)
        self.group_element_year_5 = GroupElementYearFactory(parent=self.education_group_year_3,
                                                     child_branch=self.education_group_year_1)

    def test_find_by_id(self):
        education_group_year = find_by_id(self.education_group_year_1.id)
        self.assertEqual(education_group_year, self.education_group_year_1)

        education_group_year = find_by_id(-1)
        self.assertIsNone(education_group_year)

    def test_search(self):
        result = search(id=[self.education_group_year_1.id, self.education_group_year_2.id])
        self.assertEqual(len(result), 2)

        result = search(education_group_type=self.education_group_year_2.education_group_type)
        self.assertEqual(result.first().education_group_type,
                         self.education_group_year_2.education_group_type)

        result = search(education_group_type=[self.education_group_type_training,
                                              self.education_group_type_minitraining])
        self.assertEqual(len(result), 3)

    def test_domains_property(self):
        domains = self.education_group_year_1.domains
        self.assertEqual(domains, '')

        domains = self.education_group_year_2.domains
        offer_year_domain = "{}-{} ".format(self.offer_year_domain.domain.decree, self.offer_year_domain.domain.name)
        self.assertEqual(domains, offer_year_domain)

    def test_administration_entity_property(self):
        administration_entity = self.education_group_year_1.administration_entity
        self.assertIsNone(administration_entity)

        administration_entity = self.education_group_year_2.administration_entity
        self.assertEqual(administration_entity, self.entity_version_admin)

    def test_management_entity_property(self):
        management_entity = self.education_group_year_1.management_entity
        self.assertIsNone(management_entity)

        management_entity = self.education_group_year_3.management_entity
        self.assertEqual(management_entity, self.entity_version_management)

    def test_parent_by_training_property(self):
        parent_by_training = self.education_group_year_3.is_training()
        self.assertTrue(parent_by_training)

        parent_by_training = self.education_group_year_2.parent_by_training
        self.assertIsNone(parent_by_training)

        with self.assertRaises(MaximumOneParentAllowedException):
            parent_by_training=self.education_group_year_1.parent_by_training

    def test_children_by_group_element_year_property(self):
        children_by_group_element_year = self.education_group_year_1.children_by_group_element_year
        self.assertListEqual(children_by_group_element_year, [])


class TestFindWithEnrollmentsCount(TestCase):
    """Unit tests on find_with_enrollments_count()"""
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year)
        self.education_group_year = EducationGroupYearFactory(academic_year=self.current_academic_year)
        GroupElementYearFactory(parent=self.education_group_year,
                                child_branch=None,
                                child_leaf=self.learning_unit_year)

    def test_without_learning_unit_enrollment_but_with_offer_enrollments(self):
        OfferEnrollmentFactory(education_group_year=self.education_group_year)
        result = find_with_enrollments_count(self.learning_unit_year)
        self.assertEqual(list(result), [])

    def test_with_learning_unit_enrollment_and_with_offer_enrollments(self):
        enrol_not_in_education_group = LearningUnitEnrollmentFactory(learning_unit_year=LearningUnitYearFactory())
        result = find_with_enrollments_count(enrol_not_in_education_group.learning_unit_year)
        self.assertEqual(result[0].count_learning_unit_enrollments, 1)
        self.assertEqual(result[0].count_formation_enrollments, 1)

    def test_count_learning_unit_enrollments(self):
        LearningUnitEnrollmentFactory(
            offer_enrollment=OfferEnrollmentFactory(education_group_year=self.education_group_year),
            learning_unit_year=self.learning_unit_year
        )
        result = find_with_enrollments_count(self.learning_unit_year)
        self.assertEqual(result[0].count_learning_unit_enrollments, 1)

    def test_ordered_by_acronym(self):
        group_1 = GroupElementYearFactory(parent=EducationGroupYearFactory(acronym='XDRT1234'),
                                          child_branch=None,
                                          child_leaf=self.learning_unit_year)
        group_2 = GroupElementYearFactory(parent=EducationGroupYearFactory(acronym='BMED1000'),
                                          child_branch=None,
                                          child_leaf=self.learning_unit_year)
        group_3 = GroupElementYearFactory(parent=EducationGroupYearFactory(acronym='LDROI1001'),
                                          child_branch=None,
                                          child_leaf=self.learning_unit_year)
        LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year, offer_enrollment__education_group_year=group_1.parent)
        LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year, offer_enrollment__education_group_year=group_2.parent)
        LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year, offer_enrollment__education_group_year=group_3.parent)

        result = find_with_enrollments_count(self.learning_unit_year)
        expected_list_order = [group_2.parent, group_3.parent, group_1.parent]
        self.assertEqual(list(result), expected_list_order)
