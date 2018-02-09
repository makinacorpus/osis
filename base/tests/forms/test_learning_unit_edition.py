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
import datetime

from django.test import TestCase

from base.forms.learning_unit.edition import LearningUnitEndDateForm, LearningUnitModificationForm
from base.models.enums import learning_unit_periodicity, learning_unit_year_subtypes, learning_container_year_types, \
    organization_type, entity_type, internship_subtypes
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.learning_units import LearningUnitsMixin
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person_entity import PersonEntityFactory
from reference.tests.factories.language import LanguageFactory


class TestLearningUnitEditionForm(TestCase, LearningUnitsMixin):

    def setUp(self):
        super().setUp()
        self.setup_academic_years()
        self.learning_unit = self.setup_learning_unit(
            start_year=self.current_academic_year.year,
            periodicity=learning_unit_periodicity.ANNUAL)
        self.learning_container_year = self.setup_learning_container_year(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        self.learning_unit_year = self.setup_learning_unit_year(
            academic_year=self.current_academic_year,
            learning_unit=self.learning_unit,
            learning_container_year=self.learning_container_year,
            learning_unit_year_subtype=learning_unit_year_subtypes.FULL
        )

    def test_edit_end_date_send_dates_with_end_date_not_defined(self):
        form = LearningUnitEndDateForm(None, learning_unit=self.learning_unit_year.learning_unit)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_academic_years_after_now)

    def test_edit_end_date_send_dates_with_end_date_not_defined_and_periodicity_biennal_even(self):
        self.learning_unit.periodicity = learning_unit_periodicity.BIENNIAL_EVEN
        form = LearningUnitEndDateForm(None, learning_unit=self.learning_unit_year.learning_unit)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_even_academic_years)

    def test_edit_end_date_send_dates_with_end_date_not_defined_and_periodicity_biennal_odd(self):
        self.learning_unit.periodicity = learning_unit_periodicity.BIENNIAL_ODD
        form = LearningUnitEndDateForm(None, learning_unit=self.learning_unit_year.learning_unit)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_odd_academic_years)

    def test_edit_end_date_send_dates_with_end_date_defined(self):
        self.learning_unit.end_year = self.last_academic_year.year
        form = LearningUnitEndDateForm(None, learning_unit=self.learning_unit_year.learning_unit)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_academic_years_after_now)

    def test_edit_end_date_send_dates_with_end_date_of_learning_unit_inferior_to_current_academic_year(self):
        self.learning_unit.end_year = self.oldest_academic_year.year
        form = LearningUnitEndDateForm(None, learning_unit=self.learning_unit_year.learning_unit)
        self.assertEqual(form.fields['academic_year'].disabled, True)

    def test_edit_end_date(self):
        self.learning_unit.end_year = self.last_academic_year.year
        form_data = {"academic_year": self.current_academic_year.pk}
        form = LearningUnitEndDateForm(form_data, learning_unit=self.learning_unit)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['academic_year'], self.current_academic_year)


class TestLearningUnitModificationForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.learning_container_year = LearningContainerYearFactory(academic_year=cls.current_academic_year)
        cls.learning_unit_year = LearningUnitYearFactory(academic_year=cls.current_academic_year,
                                                         learning_container_year=cls.learning_container_year,
                                                         credits=25)

        cls.organization = OrganizationFactory(type=organization_type.MAIN)
        a_campus = CampusFactory(organization=cls.organization)
        an_entity = EntityFactory(organization=cls.organization)
        cls.an_entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL, parent=None,
                                                     end_date=None,
                                                     start_date=datetime.date.today() - datetime.timedelta(days=5))
        cls.person = PersonEntityFactory(entity=an_entity).person

        language = LanguageFactory()
        cls.form_data = {
            "academic_year": str(cls.current_academic_year.id),
            "container_type": str(learning_container_year_types.COURSE),
            "subtype": str(learning_unit_year_subtypes.FULL),
            "acronym": "OSIS1452",
            "credits": "45",
            "common_title": "OSIS",
            "first_letter": "L",
            "periodicity": learning_unit_periodicity.ANNUAL,
            "campus": str(a_campus.id),
            "requirement_entity": str(cls.an_entity_version.id),
            "allocation_entity": str(cls.an_entity_version.id),
            "language": str(language.id)
        }

        cls.initial_data = {
            "academic_year": str(cls.current_academic_year.id),
            "container_type": str(learning_container_year_types.COURSE),
            "subtype": str(learning_unit_year_subtypes.FULL),
            "acronym": "OSIS1452",
            "first_letter": "L",
        }

    def test_disabled_fields_in_case_of_learning_unit_of_type_full(self):
        form = LearningUnitModificationForm(person=None, initial=self.initial_data)
        disabled_fields = ("first_letter", "acronym", "academic_year", "container_type", "subtype")
        for field in disabled_fields:
            self.assertTrue(form.fields[field].disabled)

    def test_disabled_fields_in_case_of_learning_unit_of_type_partim(self):
        initial_data_with_subtype_partim = self.initial_data.copy()
        initial_data_with_subtype_partim["subtype"] = learning_unit_year_subtypes.PARTIM
        form = LearningUnitModificationForm(person=None, initial=initial_data_with_subtype_partim)
        disabled_fields = ('first_letter', 'acronym', 'common_title', 'common_title_english', 'requirement_entity',
                           'allocation_entity', 'language', 'periodicity', 'campus', 'container_type', "academic_year",
                           'internship_subtype', 'additional_requirement_entity_1', 'additional_requirement_entity_2',
                           'is_vacant', 'team', 'type_declaration_vacant', 'attribution_procedure')
        for field in disabled_fields:
            self.assertTrue(form.fields[field].disabled)

    def test_disabled_internship_subtype_in_case_of_container_type_different_than_internship(self):
        form = LearningUnitModificationForm(person=None, initial=self.initial_data)

        self.assertTrue(form.fields["internship_subtype"].disabled)

        initial_data_with_internship_container_type = self.form_data.copy()
        initial_data_with_internship_container_type["container_type"] = learning_container_year_types.INTERNSHIP

        form = LearningUnitModificationForm(person=None, initial=initial_data_with_internship_container_type)

        self.assertFalse(form.fields["internship_subtype"].disabled)


    def test_entity_does_not_exist_for_lifetime_of_learning_unit(self):
        an_other_entity = EntityFactory(organization=self.organization)
        an_other_entity_version = EntityVersionFactory(
            entity=an_other_entity, entity_type=entity_type.SCHOOL,  parent=None,
            end_date=self.current_academic_year.end_date - datetime.timedelta(days=5),
            start_date=datetime.date.today() - datetime.timedelta(days=5))
        PersonEntityFactory(person=self.person, entity=an_other_entity)

        form_data_with_invalid_requirement_entity = self.form_data.copy()
        form_data_with_invalid_requirement_entity["requirement_entity"] = str(an_other_entity_version.id)
        form = LearningUnitModificationForm(form_data_with_invalid_requirement_entity, initial=self.initial_data,
                                            person=self.person, end_date=self.current_academic_year.end_date)
        self.assertFalse(form.is_valid())

    def test_set_max_credits(self):
        max_credits=45
        form = LearningUnitModificationForm(max_credits=max_credits, person=None, initial=self.initial_data)
        self.assertEqual(form.fields["credits"].max_value, max_credits)

    def test_entity_does_not_exist_for_lifetime_of_learning_unit_with_no_planned_end(self):
        an_other_entity = EntityFactory(organization=self.organization)
        an_other_entity_version = EntityVersionFactory(
            entity=an_other_entity, entity_type=entity_type.SCHOOL, parent=None,
            end_date=self.current_academic_year.end_date - datetime.timedelta(days=5),
            start_date=datetime.date.today() - datetime.timedelta(days=5))
        PersonEntityFactory(person=self.person, entity=an_other_entity)

        form_data_with_invalid_requirement_entity = self.form_data.copy()
        form_data_with_invalid_requirement_entity["requirement_entity"] = str(an_other_entity_version.id)
        form = LearningUnitModificationForm(form_data_with_invalid_requirement_entity,
                                            person=self.person, initial=self.initial_data)
        self.assertFalse(form.is_valid())

    def test_when_requirement_and_attribution_entities_are_different_for_disseration_and_internship_subtype(self):
        an_other_entity = EntityFactory(organization=self.organization)
        an_other_entity_version = EntityVersionFactory(entity=an_other_entity, entity_type=entity_type.SCHOOL,
                                                       parent=None, end_date=None,
                                                       start_date=datetime.date.today() - datetime.timedelta(days=5))
        form_data_with_different_allocation_entity = self.form_data.copy()
        form_data_with_different_allocation_entity["allocation_entity"] = str(an_other_entity_version.id)

        for container_type in (learning_container_year_types.DISSERTATION, learning_container_year_types.INTERNSHIP):
            initial_data_with_specific_container_type = self.initial_data.copy()
            initial_data_with_specific_container_type["container_type"] = container_type
            form = LearningUnitModificationForm(form_data_with_different_allocation_entity,
                                                person=self.person, initial=initial_data_with_specific_container_type)
            self.assertFalse(form.is_valid())

    def test_valid_form(self):
        form = LearningUnitModificationForm(self.form_data, initial=self.initial_data, person=self.person)
        self.assertTrue(form.is_valid())
