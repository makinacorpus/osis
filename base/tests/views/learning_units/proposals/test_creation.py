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
import datetime

from django.contrib.auth.models import Group, Permission
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm, LearningUnitYearModelForm, \
    LearningContainerYearModelForm
from base.forms.learning_unit_proposal import ProposalLearningUnitForm, CreationProposalBaseForm
from base.models.enums import learning_unit_year_subtypes, learning_container_year_types, organization_type, \
    entity_type, learning_unit_periodicity
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import FACULTY_MANAGER_GROUP
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.tests.factories import campus as campus_factory, \
    organization as organization_factory, person as factory_person, user as factory_user
from base.tests.factories.academic_year import get_current_year
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.views.learning_units.proposal.create import get_proposal_learning_unit_creation_form
from reference.tests.factories.language import LanguageFactory


class LearningUnitViewTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.faculty_user = factory_user.UserFactory()
        self.faculty_user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        self.faculty_person = factory_person.PersonFactory(user=self.faculty_user)
        self.faculty_user.user_permissions.add(Permission.objects.get(codename='can_propose_learningunit'))
        self.faculty_user.user_permissions.add(Permission.objects.get(codename='can_create_learningunit'))
        self.super_user = factory_user.SuperUserFactory()
        self.person = factory_person.PersonFactory(user=self.super_user)
        self.academic_years = GenerateAcademicYear(get_current_year(), get_current_year() + 7).academic_years
        self.academic_year = self.academic_years[0]

        self.language = LanguageFactory(code='FR')
        self.organization = organization_factory.OrganizationFactory(type=organization_type.MAIN)
        self.campus = campus_factory.CampusFactory(organization=self.organization, is_administration=True)
        self.entity = EntityFactory(organization=self.organization)
        self.entity_version = EntityVersionFactory(entity=self.entity, entity_type=entity_type.SCHOOL,
                                                   start_date=today - datetime.timedelta(days=1),
                                                   end_date=self.academic_years[-1].end_date)

        PersonEntityFactory(person=self.faculty_person, entity=self.entity)
        PersonEntityFactory(person=self.person, entity=self.entity)

    def get_valid_data(self):
        return {
            'acronym_0': 'L',
            'acronym_1': 'TAU2000',
            "subtype": learning_unit_year_subtypes.FULL,
            "container_type": learning_container_year_types.COURSE,
            "academic_year": self.academic_year.id,
            "status": True,
            "credits": "5",
            "campus": self.campus.id,
            "common_title": "Common UE title",
            "language": self.language.pk,
            "periodicity": learning_unit_periodicity.ANNUAL,
            "entity": self.entity_version.id,
            "folder_id": 1,
            'entitycontaineryear_set-0-entity': self.entity_version.id,
            'entitycontaineryear_set-1-entity': self.entity_version.id,
            'entitycontaineryear_set-2-entity': '',
            'entitycontaineryear_set-INITIAL_FORMS': '0',
            'entitycontaineryear_set-MAX_NUM_FORMS': '4',
            'entitycontaineryear_set-MIN_NUM_FORMS': '3',
            'entitycontaineryear_set-TOTAL_FORMS': '4',
        }

    def test_get_proposal_learning_unit_creation_form(self):
        self.client.force_login(self.person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.academic_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/creation.html')
        self.assertIsInstance(response.context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

    def test_get_proposal_learning_unit_creation_form_with_faculty_user(self):
        self.client.force_login(self.faculty_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.academic_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/creation.html')
        self.assertIsInstance(response.context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

    def test_post_proposal_learning_unit_creation_form(self):
        self.client.force_login(self.person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.academic_year.id])
        response = self.client.post(url, data=self.get_valid_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 1)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.person).count()
        self.assertEqual(count_proposition_by_author, 1)

    def test_post_proposal_learning_unit_creation_form_with_faculty_user(self):
        self.client.force_login(self.faculty_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.academic_year.id])
        response = self.client.post(url, data=self.get_valid_data())

        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 1)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.faculty_person).count()
        self.assertEqual(count_proposition_by_author, 1)

    def get_invalid_data(self):
        faultydict = dict(self.get_valid_data())
        faultydict["acronym_1"] = "T2"
        faultydict["acronym_0"] = "A"
        return faultydict

    def test_proposal_learning_unit_add_with_invalid_data(self):
        self.client.force_login(self.person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.academic_year.id])
        response = self.client.post(url, data=self.get_invalid_data())
        self.assertEqual(response.status_code, 200)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 0)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.person).count()
        self.assertEqual(count_proposition_by_author, 0)

    def get_empty_required_fields(self):
        faultydict = dict(self.get_valid_data())
        faultydict["acronym_0"] = ""
        faultydict["container_type"] = ""
        faultydict["campus"] = ""
        faultydict["periodicity"] = ""
        faultydict["language"] = ""
        return faultydict

    def get_empty_title_fields(self):
        faultydict = dict(self.get_valid_data())
        faultydict["specific_title"] = None
        faultydict["common_title"] = None
        return faultydict

    def test_proposal_learning_unit_form_with_empty_fields(self):
        learning_unit_form = CreationProposalBaseForm(self.get_empty_required_fields(), person=self.person)
        self.assertFalse(learning_unit_form.is_valid(), learning_unit_form.errors)
        luy_errors = learning_unit_form.learning_unit_form_container.forms[LearningUnitYearModelForm].errors
        lu_errors = learning_unit_form.learning_unit_form_container.forms[LearningUnitModelForm].errors
        lcy_errors = learning_unit_form.learning_unit_form_container.forms[LearningContainerYearModelForm].errors

        self.assertEqual(luy_errors['acronym'], [_('field_is_required'), _('invalid_acronym')])
        self.assertEqual(lcy_errors['container_type'], [_('field_is_required')])
        self.assertEqual(lu_errors['periodicity'], [_('field_is_required')])
        self.assertEqual(lcy_errors['language'], [_('field_is_required')])
        self.assertEqual(lcy_errors['campus'], [_('field_is_required')])

    def test_proposal_learning_unit_form_with_empty_title_fields(self):
        learning_unit_form = CreationProposalBaseForm(self.get_empty_title_fields(), person=self.person)
        self.assertFalse(learning_unit_form.is_valid(), learning_unit_form.errors)
        lcy_errors = learning_unit_form.learning_unit_form_container.forms[LearningContainerYearModelForm].errors
        self.assertEqual(lcy_errors['common_title'], [_('must_set_common_title_or_specific_title')])

    def test_proposal_learning_unit_add_with_valid_data_for_faculty_manager(self):
        learning_unit_form = CreationProposalBaseForm(self.get_valid_data(), person=self.faculty_person)

        self.assertTrue(learning_unit_form.is_valid(), learning_unit_form.errors)
        self.client.force_login(self.faculty_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.academic_year.id])
        response = self.client.post(url, data=self.get_valid_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 1)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.faculty_person).count()
        self.assertEqual(count_proposition_by_author, 1)
