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
from django.test import TestCase
from base.models import offer_enrollment
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories import academic_year
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory


def create_date_enrollment():
    return datetime.date.today()


def create_offer_enrollment(student, offer_year):
    an_offer_enrollment = offer_enrollment.OfferEnrollment(date_enrollment=create_date_enrollment(),
                                                           student=student, offer_year=offer_year)
    an_offer_enrollment.save()
    return an_offer_enrollment


class OfferEnrollementTest(TestCase):
    def test_find_by_offers_year(self):
        student1 = StudentFactory.create()
        offer_year1 = OfferYearFactory()
        OfferEnrollmentFactory(student=student1, offer_year=offer_year1)
        result = list(offer_enrollment.find_by_offers_years([offer_year1]))
        self.assertEqual(result[0].student, student1)
        self.assertEqual(result[0].offer_year, offer_year1)
        self.assertEqual(len(result), 1)
