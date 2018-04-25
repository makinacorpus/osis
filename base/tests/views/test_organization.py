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

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from base.models import organization_address
from base.models.organization import Organization
from base.models.organization_address import OrganizationAddress
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.user import SuperUserFactory
from django.utils.translation import ugettext_lazy as _


class OrganizationViewTestCase(TestCase):

    def setUp(self):
        self.organization = OrganizationFactory()
        self.a_superuser = SuperUserFactory()
        self.client.force_login(self.a_superuser)

    def test_organization_save(self):
        from base.views.organization import organization_save
        url = reverse(organization_save, args=[self.organization.id])
        response = self.client.post(url, data=get_form_organization_save())
        self.organization.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.organization.acronym, "NYU")
        self.assertEqual(self.organization.name, "NEW-YORK UNIVERSITY")

    def test_organization_address_save(self):
        from base.views.organization import organization_address_save

        address = OrganizationAddressFactory(organization=self.organization)
        country = address.country
        url = reverse(organization_address_save, args=[address.id])
        response = self.client.post(url, data=get_form_organization_address_save())
        address.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(address.location, "476 5th Ave")
        self.assertEqual(address.postal_code, "10018")
        self.assertEqual(address.city, "New York")
        self.assertEqual(address.country, country)

    @mock.patch('base.views.layout.render')
    def test_organization_address_create(self, mock_render):
        from base.views.organization import organization_address_create

        request_factory = RequestFactory()
        request = request_factory.get(reverse(organization_address_create, args=[self.organization.id]))
        request.user = mock.Mock()

        organization_address_create(request, self.organization.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, "organization_address_form.html")
        self.assertIsInstance(context.get("organization_address"), OrganizationAddress)
        self.assertEqual(context.get("organization_id"), self.organization.id)

    @mock.patch('base.views.layout.render')
    def test_organization_address_delete(self, mock_render):
        from base.views.organization import organization_address_delete
        address = OrganizationAddressFactory(organization=self.organization)

        request_factory = RequestFactory()
        request = request_factory.get(reverse(organization_address_delete, args=[address.id]))
        request.user = mock.Mock()

        organization_address_delete(request, address.id)

        self.assertTrue(mock_render.called)
        with self.assertRaises(ObjectDoesNotExist):
            organization_address.find_by_id(address.id)

    @mock.patch('base.views.layout.render')
    def test_organization_address_edit(self, mock_render):
        from base.views.organization import organization_address_edit
        address = OrganizationAddressFactory(organization=self.organization)
        request_factory = RequestFactory()
        request = request_factory.get(reverse(organization_address_edit, args=[address.id]))
        request.user = mock.Mock()

        organization_address_edit(request, address.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, "organization_address_form.html")
        self.assertEqual(context.get("organization_address"), address)
        self.assertEqual(context.get("organization_id"), self.organization.id)

    def test_organization_address_new_empty(self):
        from base.views.organization import organization_address_new
        from django.contrib.messages.storage.fallback import FallbackStorage

        request_factory = RequestFactory()
        request = request_factory.get(reverse(organization_address_new))
        request.user = mock.Mock()
        # Need session in order to store messages
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        organization_address_new(request)
        self.assertEqual(str(request._messages._queued_messages[0]), _("organization_address_save_error"))

    @mock.patch('base.views.layout.render')
    def test_organizations_search(self, mock_render):
        from base.views.organization import organizations_search
        request_factory = RequestFactory()
        request = request_factory.get(reverse(organizations_search), data={
            'acronym':  self.organization.acronym[:2]
        })
        request.user = mock.Mock()
        organizations_search(request)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, "organizations.html")
        self.assertEqual(context["organizations"][0], self.organization)

    @mock.patch('base.views.layout.render')
    def test_organization_create(self, mock_render):
        from base.views.organization import organization_create
        request_factory = RequestFactory()
        request = request_factory.get(reverse(organization_create))
        request.user = mock.Mock()
        organization_create(request)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, "organization_form.html")
        self.assertIsInstance(context["organization"], Organization)

    @mock.patch('base.views.layout.render')
    def test_organization_edit(self, mock_render):
        from base.views.organization import organization_edit
        request_factory = RequestFactory()
        request = request_factory.get(reverse(organization_edit, args=[self.organization.id]))
        request.user = mock.Mock()
        organization_edit(request, self.organization.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, "organization_form.html")
        self.assertEqual(context["organization"], self.organization)


def get_form_organization_save():
    return {
        "acronym": "NYU",
        "name": "NEW-YORK UNIVERSITY",
        "website": "www.nyu.edu",
        "prefix": "NYUA"
    }


def get_form_organization_address_save():
    return {
        "organization_address_label": "Building",
        "organization_address_location": "476 5th Ave",
        "organization_address_postal_code": "10018",
        "organization_address_city": "New York"
    }
