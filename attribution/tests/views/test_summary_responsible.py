##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from attribution.tests.models import test_attribution
from base.models.entity_manager import EntityManager

from base.tests.factories import structure
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.entities import create_entities_hierarchy
from base.tests.factories.business.learning_units import create_learning_unit_with_context
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


class SummaryResponsibleViewTestCase(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.user = self.person.user
        self.tutor = TutorFactory(person=self.person)
        self.academic_year = AcademicYearFactory(year=datetime.date.today().year,
                                                 start_date=datetime.date.today())
        # Old structure model [To remove]
        self.structure = structure.StructureFactory()
        self.structure_children = structure.StructureFactory(part_of=self.structure)

        # New structure model
        entities_hierarchy = create_entities_hierarchy()
        self.root_entity = entities_hierarchy.get('root_entity')
        self.child_one_entity = entities_hierarchy.get('child_one_entity')
        self.child_two_entity = entities_hierarchy.get('child_two_entity')

        self.entity_manager = EntityManagerFactory(
            person=self.person,
            structure=self.structure,
            entity=self.root_entity)

        # Create two learning_unit_year with context (Container + EntityContainerYear)
        self.learning_unit_year = create_learning_unit_with_context(
            academic_year=self.academic_year,
            structure=self.structure,
            entity=self.child_one_entity,
            acronym="LBIR1210")
        self.learning_unit_year_children = create_learning_unit_with_context(
            academic_year=self.academic_year,
            structure=self.structure_children,
            entity=self.child_two_entity,
            acronym="LBIR1211")

        self.attribution = test_attribution.create_attribution(
            tutor=self.tutor,
            learning_unit_year=self.learning_unit_year,
            summary_responsible=True)
        self.attribution_children = test_attribution.create_attribution(
            tutor=self.tutor,
            learning_unit_year=self.learning_unit_year_children,
            summary_responsible=True)

    def test_user_not_logged(self):
        url = reverse("summary_responsible")
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(response, '/login/?next={}'.format(url))

    def test_user_is_not_entity_manager(self):
        url = reverse("summary_responsible")
        entity_managers = EntityManager.objects.filter(person__user=self.user)
        entity_managers.delete()

        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/login/?next={}'.format(url))

    def test_summary_responsible_search_with_two_criteria(self):
        url = reverse("summary_responsible")
        self.client.force_login(self.user)
        data = {
            'course_code': 'LBIR121',
            'learning_unit_title': '',
            'tutor': self.person.last_name,
            'summary_responsible': ''
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context[-1]['dict_attribution'],
                              [self.attribution, self.attribution_children])

    def test_summary_responsible_search_without_criteria(self):
        url = reverse("summary_responsible")
        self.client.force_login(self.user)
        data = {
            'course_code': '',
            'learning_unit_title': '',
            'tutor': '',
            'summary_responsible': ''
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context[-1]['dict_attribution'],
                         [self.attribution, self.attribution_children])