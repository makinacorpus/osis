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
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.contrib.messages.api import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage

from base.models import tutor
from django.test import TestCase

from base.tests.factories.tutor import TutorFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory


def create_tutor(first_name="Tutor", last_name="tutor"):
    return TutorFactory(
        person=PersonFactory(first_name=first_name, last_name=last_name)
    )


def create_tutor_with_person(person):
    return TutorFactory(person=person)


class TestTutor(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.person = PersonFactory(first_name="James", last_name="Dupont", user=self.user)
        self.tutor = TutorFactory(person=self.person)
        TutorFactory()  # Create fake Tutor
        TutorFactory()  # Create fake Tutor

    def test_find_by_person(self):
        self.assertEqual(self.tutor, tutor.find_by_person(self.person))

    def test_find_by_person_empty(self):
        person_unknown = PersonFactory()
        self.assertIsNone(tutor.find_by_person(person_unknown))

    def test_find_by_person_wrong_id(self):
        self.assertIsNone(tutor.find_by_person(-1))

    def test_is_tutor(self):
        self.assertTrue(tutor.is_tutor(self.user))

    def test_is_not_tutor(self):
        user_unknown = UserFactory()
        self.assertFalse(tutor.is_tutor(user_unknown))

    def test_find_by_user(self):
        self.assertEqual(self.tutor, tutor.find_by_user(self.user))

    def test_find_by_user_wrong_id(self):
        self.assertIsNone(tutor.find_by_user(-1))

    def test_find_by_id(self):
        self.assertEqual(self.tutor, tutor.find_by_id(self.tutor.id))

    def test_find_by_id_wrong_id(self):
        self.assertIsNone(tutor.find_by_id(-1))


class MockRequest:
    COOKIES={}


class MockSuperUser:
    def has_perm(self, perm):
        return True


request = MockRequest()
request.user = MockSuperUser()


class TestTutorAdmin(TestCase):
    def setUp(self):
        for _ in range(10):
            user = UserFactory()
            person = PersonFactory(user=user)
            TutorFactory(person=person)
            user.groups.clear()

        self.site = AdminSite()

    def test_add_to_group(self):
        setattr(request, 'session', 'session')
        msg = FallbackStorage(request)
        setattr(request, '_messages', msg)
        tutor_admin = tutor.TutorAdmin(tutor.Tutor, self.site)
        queryset = tutor.Tutor.objects.all()
        tutor_admin.add_to_group(request, queryset)
        msg = [m.message for m in get_messages(request)]
        self.assertIn("{} users added to the group 'tutors'.".format(10), msg)

    def test_add_to_group_no_tutor_group(self):
        setattr(request, 'session', 'session')
        msg = FallbackStorage(request)
        setattr(request, '_messages', msg)
        for group in Group.objects.all():
            group.delete()
        tutor_admin = tutor.TutorAdmin(tutor.Tutor, self.site)
        queryset = tutor.Tutor.objects.all()
        tutor_admin.add_to_group(request, queryset)
        msg = [m.message for m in get_messages(request)]
        self.assertIn("Group tutors doesn't exist.", msg)
