##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.forms.learning_unit.edition import LearningUnitEndDateForm
from base.models.enums import learning_unit_year_periodicity, learning_unit_year_subtypes, learning_container_year_types
from base.tests.factories.business.learning_units import LearningUnitsMixin


class TestLearningUnitEditionForm(TestCase, LearningUnitsMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.setup_academic_years()
        cls.learning_unit = cls.setup_learning_unit(
            start_year=cls.starting_academic_year)
        cls.learning_container_year = cls.setup_learning_container_year(
            academic_year=cls.starting_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        cls.learning_unit_year = cls.setup_learning_unit_year(
            academic_year=cls.starting_academic_year,
            learning_unit=cls.learning_unit,
            learning_container_year=cls.learning_container_year,
            learning_unit_year_subtype=learning_unit_year_subtypes.FULL,
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

    def test_edit_end_date_send_dates_with_end_date_not_defined(self):
        form = LearningUnitEndDateForm(None, learning_unit_year=self.learning_unit_year)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_academic_years_after_now)

    def test_edit_end_date_send_dates_with_end_date_defined(self):
        self.learning_unit.end_year = self.last_academic_year
        form = LearningUnitEndDateForm(None, learning_unit_year=self.learning_unit_year)
        self.assertEqual(list(form.fields['academic_year'].queryset), self.list_of_academic_years_after_now)

    def test_edit_end_date_send_dates_with_end_date_of_learning_unit_inferior_to_current_academic_year(self):
        self.learning_unit.end_year = self.oldest_academic_year
        form = LearningUnitEndDateForm(None, learning_unit_year=self.learning_unit_year)
        self.assertEqual(form.fields['academic_year'].disabled, True)

    def test_edit_end_date(self):
        self.learning_unit.end_year = self.last_academic_year
        form_data = {"academic_year": self.starting_academic_year.pk}
        form = LearningUnitEndDateForm(form_data, learning_unit_year=self.learning_unit_year)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['academic_year'], self.starting_academic_year)
