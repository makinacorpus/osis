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
from base.models import organization
from base.tests.factories.organization import OrganizationFactory
from base.models.enums import organization_type


ACRONYM_ORG_1 = "ORG-1"
NAME_ORG_1 = "organization1"
TYPE_ORG_1_AND_2 = organization_type.ACADEMIC_PARTNER


class OrganizationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization_1 = OrganizationFactory(acronym=ACRONYM_ORG_1,
                                                 name=NAME_ORG_1,
                                                 type=TYPE_ORG_1_AND_2)
        cls.organization_2 = OrganizationFactory(acronym="ORG-2",
                                                 name="organization2",
                                                 type=TYPE_ORG_1_AND_2)

    def test_search_no_result(self):
        self.assertIsNone(organization.search(None, None, None))
        self.assertEqual(len(organization.search("ORG-55", None, None)), 0)
        self.assertEqual(len(organization.search(ACRONYM_ORG_1, "organization name unknown", None)), 0)
        self.assertEqual(len(organization.search(ACRONYM_ORG_1, NAME_ORG_1, organization_type.COMMERCE_PARTNER)), 0)

    def test_search_with_results(self):
        result = organization.search(ACRONYM_ORG_1, None, None)
        self.assertCountEqual(result, [self.organization_1])
        result = organization.search(None, NAME_ORG_1, None)
        self.assertCountEqual(result, [self.organization_1])
        result = organization.search(None, None, TYPE_ORG_1_AND_2)
        self.assertCountEqual(result, [self.organization_1, self.organization_2])
        result = organization.search("ORG-", None, None)
        self.assertCountEqual(result, [self.organization_1, self.organization_2])
        result = organization.search("org-", None, None)
        self.assertCountEqual(result, [self.organization_1, self.organization_2])
        result = organization.search(None, NAME_ORG_1.lower(), None)
        self.assertCountEqual(result, [self.organization_1])
