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
import datetime

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.forms.learning_unit_proposal import LearningUnitProposalModificationForm


@login_required
def propose_modification_of_learning_unit(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, id=learning_unit_year_id)
    user_person = get_object_or_404(Person, user=request.user)
    initial_data = {
        "academic_year": learning_unit_year.academic_year.pk,
        "first_letter": learning_unit_year.acronym[0],
        "acronym": learning_unit_year.acronym[1:],
        "title": learning_unit_year.title,
        "title_english": learning_unit_year.title_english,
        "subtype": learning_unit_year.subtype,
        "internship_subtype": learning_unit_year.internship_subtype,
        "credits": learning_unit_year.credits,
        "periodicity": learning_unit_year.learning_unit.periodicity,
        "status": learning_unit_year.status,
        "language": learning_unit_year.learning_container_year.language,
        "quadrimester": learning_unit_year.quadrimester,
        "campus": learning_unit_year.learning_container_year.campus,
        "person": user_person.pk,
        "date": datetime.date.today()
    }
    form = LearningUnitProposalModificationForm(initial=initial_data)
    return render(request, 'proposal/learning_unit_modification.html', {'learning_unit_year': learning_unit_year,
                                                                        'person': user_person,
                                                                        'form': form,
                                                                        'experimental_phase': True})
