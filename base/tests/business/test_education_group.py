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
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from base.business.education_group import can_user_edit_administrative_data
from base.models.enums import offer_year_entity_type
from base.models.person import Person, CENTRAL_MANAGER_GROUP
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory


class EducationGroupTestCase(TestCase):
    def setUp(self):
        # Get or Create Permission to edit administrative data
        content_type = ContentType.objects.get_for_model(Person)
        permission, created = Permission.objects.get_or_create(
            codename="can_edit_education_group_administrative_data",
            content_type=content_type)
        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(permission)
        # Create structure
        self._create_basic_entity_structure()
        # Create education group with 'CHIM' as entity management
        self.education_group_year = EducationGroupYearFactory()
        OfferYearEntityFactory(education_group_year=self.education_group_year,
                               type=offer_year_entity_type.ENTITY_MANAGEMENT,
                               entity=self.chim_entity)

    def test_can_user_edit_administrative_data_no_permission(self):
        """Without permission/group, we cannot access to administrative data ==> Refused"""
        user_without_perm = UserFactory()
        self.assertFalse(can_user_edit_administrative_data(user_without_perm, self.education_group_year))

    def test_can_user_edit_administrative_data_with_permission_no_pgrm_manager(self):
        """With permission but no program manager of education group ==> Refused"""
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administrative_data_with_permission_and_pgrm_manager(self):
        """With permission and program manager of education group ==> Allowed"""
        ProgramManagerFactory(person=self.person, education_group=self.education_group_year.education_group)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_no_entity_linked(self):
        """With permission + Group central manager + No linked to the right entity + Not program manager ==> Refused """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_entity_linked(self):
        """With permission + Group central manager + Linked to the right entity ==> Allowed """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.chim_entity, with_child=False)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_parent_entity_linked_with_child(self):
        """With permission + Group central manager + Linked to the parent entity (with child TRUE) ==> Allowed """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.root_entity, with_child=True)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_parent_entity_linked_no_child(self):
        """With permission + Group central manager + Linked to the parent entity (with child FALSE) ==> Refused """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.root_entity, with_child=False)
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_no_entity_linked_but_program_manager(self):
        """With permission + Group central manager + Linked to the parent entity (with_child FALSE) + IS program manager ==> Allowed """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.root_entity, with_child=False)
        ProgramManagerFactory(person=self.person, education_group=self.education_group_year.education_group)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def _create_basic_entity_structure(self):
        self.organization = OrganizationFactory(name="Université catholique de Louvain", acronym="UCL")
        # Create entities UCL
        self.root_entity = _create_entity_and_version_related_to(self.organization, "UCL")
        # SST entity
        self.sst_entity = _create_entity_and_version_related_to(self.organization, "SST", self.root_entity)
        self.agro_entity = _create_entity_and_version_related_to(self.organization, "AGRO", self.sst_entity)
        self.chim_entity = _create_entity_and_version_related_to(self.organization, "CHIM", self.sst_entity)


def _create_entity_and_version_related_to(organization, acronym, parent=None):
    entity = EntityFactory(organization=organization)
    EntityVersionFactory(acronym=acronym, entity=entity, parent=parent, end_date=None)
    return entity


def _add_to_group(user, group_name):
    group, created = Group.objects.get_or_create(name=group_name)
    group.user_set.add(user)
