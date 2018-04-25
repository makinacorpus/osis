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

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied

from base.models.enums import learning_unit_year_subtypes
from base.models.learning_achievement import LearningAchievement
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from reference.tests.factories.language import LanguageFactory
from base.views.learning_achievement import operation, management, DELETE, DOWN, UP
from base.forms.learning_achievement import LearningAchievementEditForm
from base.tests.factories.user import SuperUserFactory


class TestLearningAchievementView(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )

        self.language_fr = LanguageFactory(code="FR")
        self.user = UserFactory()
        PersonFactory(user=self.user)
        self.client.force_login(self.user)
        self.achievement_fr = LearningAchievementFactory(language=self.language_fr,
                                                         learning_unit_year=self.learning_unit_year,
                                                         order=0)

    def test_operation_method_not_allowed(self):
        request_factory = RequestFactory()
        request = request_factory.post(reverse('achievement_management',
                                               args=[self.achievement_fr.learning_unit_year.id]),
                                       data={'achievement_id': self.achievement_fr.id,
                                             'action': DELETE})
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            management(request, self.achievement_fr.learning_unit_year.id)

    def test_delete_redirection(self):
        request_factory = RequestFactory()
        request = request_factory.post(reverse('achievement_management',
                                               args=[self.achievement_fr.learning_unit_year.id]),
                                       data={'achievement_id': self.achievement_fr.id,
                                             'action': DELETE})
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        request.user = self.user

        response = management(request, self.achievement_fr.learning_unit_year.id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         "/learning_units/{}/specifications/".format(self.achievement_fr.learning_unit_year.id))


class TestLearningAchievementActions(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )

        self.language_fr = LanguageFactory(code="FR")
        self.language_en = LanguageFactory(code="EN")
        self.user = UserFactory()
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))

        PersonFactory(user=self.user)
        self.client.force_login(self.user)
        self.a_superuser = SuperUserFactory()

    def test_delete(self):
        achievement_fr_0 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year,
                                                      order=0)
        achievement_en_0 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year,
                                                      order=0)
        achievement_fr_1 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year,
                                                      order=1)
        LearningAchievementFactory(language=self.language_en,
                                   learning_unit_year=self.learning_unit_year,
                                   order=1)
        request_factory = RequestFactory()
        request = request_factory.post(management)
        request.user = self.user
        operation(achievement_fr_1.id, 'delete')
        self.assertCountEqual(LearningAchievement.objects.all(), [achievement_fr_0,
                                                                  achievement_en_0])

    def test_up(self):
        achievement_fr_0 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_0 = achievement_fr_0.id
        achievement_en_0 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_0 = achievement_en_0.id
        achievement_fr_1 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_1 = achievement_fr_1.id
        achievement_en_1 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_1 = achievement_en_1.id

        request_factory = RequestFactory()
        request = request_factory.post(management)
        request.user = self.user
        operation(achievement_fr_1.id, UP)

        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_1).order, 0)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_1).order, 0)

    def test_down(self):
        achievement_fr_0 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_0 = achievement_fr_0.id
        achievement_en_0 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_0 = achievement_en_0.id
        achievement_fr_1 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_1 = achievement_fr_1.id
        achievement_en_1 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_1 = achievement_en_1.id

        request_factory = RequestFactory()
        request = request_factory.post(reverse('achievement_management', args=[achievement_fr_0.learning_unit_year.id]))
        request.user = self.user
        operation(achievement_fr_0.id, DOWN)

        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_1).order, 0)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_1).order, 0)

    @mock.patch('base.views.layout.render')
    def test_learning_achievement_edit(self, mock_render):

        learning_unit_year = LearningUnitYearFactory()
        learning_achievement = LearningAchievementFactory(learning_unit_year=learning_unit_year)

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit',
                                              args=[learning_unit_year.id]), data={
            'achievement_id': learning_achievement.id
        })
        request.user = self.a_superuser

        from base.views.learning_achievement import edit

        edit(request, learning_unit_year.id, learning_achievement.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/achievement_edit.html')
        self.assertIsInstance(context['form'], LearningAchievementEditForm)

    def test_learning_achievement_save(self):
        learning_unit_year = LearningUnitYearFactory()
        learning_achievement = LearningAchievementFactory(learning_unit_year=learning_unit_year,
                                                          language=self.language_fr)
        response = self.client.post(reverse('achievement_edit',
                                            kwargs={'learning_unit_year_id': learning_unit_year.id,
                                                    'learning_achievement_id': learning_achievement.id}), data={'code_name': 'AA1', 'text': 'Text'})

        expected_redirection = reverse("learning_unit_specifications",
                                       kwargs={'learning_unit_year_id': learning_unit_year.id})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)
