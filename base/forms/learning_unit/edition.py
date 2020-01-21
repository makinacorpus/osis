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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django import forms
from django.utils.translation import gettext_lazy as _

from base.business import event_perms
from base.business.learning_units.edition import edit_learning_unit_end_date
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.models.academic_year import AcademicYear


# TODO Convert it in ModelForm
class LearningUnitEndDateForm(forms.Form):
    academic_year = forms.ModelChoiceField(required=True,
                                           queryset=AcademicYear.objects.none(),
                                           empty_label=BLANK_CHOICE_DISPLAY,
                                           label=_('Last year of organization')
                                           )

    def __init__(self, data, learning_unit_year, *args, max_year=None, person=None, proposal_context=False, **kwargs):
        self.learning_unit = learning_unit_year.learning_unit
        self.learning_unit_year = learning_unit_year
        self.person = person
        self.proposal_context = proposal_context
        super().__init__(data, *args, **kwargs)
        end_year = self.learning_unit.end_year

        self._set_initial_value(end_year)

        try:
            self.fields['academic_year'].queryset = self._get_academic_years(max_year)
        except ValueError:
            self.fields['academic_year'].disabled = True

        if max_year:
            self.fields['academic_year'].required = True

    def _set_initial_value(self, end_year):
        self.fields['academic_year'].initial = end_year

    def _get_academic_years(self, max_year):
        if self.learning_unit.is_past():
            raise ValueError(
                'Learning_unit.end_year {} cannot be less than the current academic_year'.format(
                    self.learning_unit.end_year)
            )

        if self.proposal_context:
            event_perm = event_perms.generate_event_perm_creation_end_date_proposal(self.person)
        else:
            event_perm = event_perms.generate_event_perm_learning_unit_edition(self.person)

        luy_current_year = self.learning_unit_year.academic_year.year
        academic_years = event_perm.get_academic_years(min_academic_y=luy_current_year, max_academic_y=max_year)

        return academic_years

    def save(self, update_learning_unit_year=True):
        return edit_learning_unit_end_date(self.learning_unit, self.cleaned_data['academic_year'],
                                           update_learning_unit_year)
