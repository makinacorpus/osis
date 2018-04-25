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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import json
from django.test import TestCase
from base.tests.factories.person import PersonFactory
from dissertation.tests.factories.adviser import AdviserManagerFactory, AdviserTeacherFactory


ERROR_405_BAD_REQUEST=405
ERROR_404_PAGE_NO_FOUND = 404
NO_ERROR_CODE = 200
ERROR_403_NOT_AUTORIZED=403

class UtilsTestCase(TestCase):
    def setUp(self):
        self.manager = AdviserManagerFactory()
        a_person_teacher = PersonFactory.create(first_name='Pierre', last_name='Dupont')
        self.teacher = AdviserTeacherFactory(person=a_person_teacher)

    def test_find_adviser_list_json(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.get('/dissertation/find_adviser_list/',
                                   {'term': 'Dupont'})
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, NO_ERROR_CODE)
        self.assertEqual(len(response_data), 1)
