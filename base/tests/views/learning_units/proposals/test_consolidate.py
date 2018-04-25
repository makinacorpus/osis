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
from unittest import mock

from django.contrib.auth.models import Permission
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from rest_framework.reverse import reverse

from base.models.enums import proposal_state, entity_container_year_link_type
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory


class TestConsolidate(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_current_academic_year()

        cls.proposal = ProposalLearningUnitFactory(state=proposal_state.ProposalState.ACCEPTED.name)
        cls.learning_unit_year = cls.proposal.learning_unit_year

        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_consolidate_learningunit_proposal"))

        PersonEntityFactory(person=cls.person,
                            entity=EntityContainerYearFactory(
                                learning_container_year=cls.learning_unit_year.learning_container_year,
                                type=entity_container_year_link_type.REQUIREMENT_ENTITY).entity
                            )

        cls.url = reverse("learning_unit_consolidate_proposal")
        cls.post_data = {"learning_unit_year_id": cls.learning_unit_year.id}

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_login_required(self):
        self.client.logout()

        response = self.client.post(self.url, data=self.post_data)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_accepts_only_post_request(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "method_not_allowed.html")
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    def test_when_no_permission_to_consolidate(self):
        person_with_no_rights = PersonFactory()
        self.client.force_login(person_with_no_rights.user)
        response = self.client.post(self.url, data=self.post_data)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_when_no_proposal(self):
        post_data = {"learning_unit_year_id": self.learning_unit_year.id + 1}

        response = self.client.post(self.url, data=post_data)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_when_no_post_data(self):
        response = self.client.post(self.url, data={})

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch("base.business.learning_unit_proposal.consolidate_proposals_and_send_report",
                side_effect=lambda prop, author, send_mail: {})
    def test_when_proposal_and_can_consolidate_proposal(self, mock_consolidate):
        response = self.client.post(self.url, data=self.post_data, follow=False)

        expected_redirect_url = reverse('learning_unit', args=[self.learning_unit_year.id])
        self.assertRedirects(response, expected_redirect_url)
        mock_consolidate.assert_called_once_with([self.proposal], self.person, {})
