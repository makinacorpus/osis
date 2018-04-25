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
from dissertation.models import adviser
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from base.models.student import find_by_offer_year
from base.models.offer_year import OfferYear
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
MAX_RETURN = 50


@login_required
@user_passes_test(adviser.is_manager)
def get_students_list_in_offer_year(request, offer_year_start_id):
    offer_year_start = get_object_or_404(OfferYear, pk=offer_year_start_id)
    students_list = find_by_offer_year(offer_year_start)
    data=[]
    if students_list:
        for student in students_list:
            data.append({'person_id': student.id,
                         'first_name': student.person.first_name,
                         'last_name': student.person.last_name,
                         'registration_id': student.registration_id})

    else:
        data = False

    return JsonResponse({'res': data})


@login_required
@user_passes_test(adviser.is_manager)
def find_adviser_list_json(request):
    term_search = request.GET.get('term')
    advisers = adviser.find_advisers_last_name_email(term_search, MAX_RETURN)
    response_data = adviser.convert_advisers_to_array(advisers)
    return JsonResponse(response_data, safe=False)
