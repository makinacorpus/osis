##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from base.models.entity_calendar import find_by_entity_and_reference_for_current_academic_year
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION, EXAM_ENROLLMENTS
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity_calendar import EntityCalendarFactory


class TestFindByReferenceForCurrentAcademicYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_academic_year = create_current_academic_year()
        previous_academic_year = AcademicYearFactory(year=current_academic_year.year-1)

        cls.current_entity_calendar = EntityCalendarFactory(academic_calendar__academic_year=current_academic_year,
                                                        academic_calendar__reference=SUMMARY_COURSE_SUBMISSION)
        previous_entity_calendar = EntityCalendarFactory(academic_calendar__academic_year=previous_academic_year,
                                                         academic_calendar__reference=SUMMARY_COURSE_SUBMISSION,
                                                         entity=cls.current_entity_calendar.entity)

    def test_when_no_data_match_criteria(self):
        entity_calendar_obj = find_by_entity_and_reference_for_current_academic_year(
            self.current_entity_calendar.entity.id, EXAM_ENROLLMENTS)
        self.assertIsNone(entity_calendar_obj)

    def test_find_for_current_academic_year(self):
        entity_calendar_obj = find_by_entity_and_reference_for_current_academic_year(
            self.current_entity_calendar.entity.id, SUMMARY_COURSE_SUBMISSION)
        self.assertEqual(entity_calendar_obj, self.current_entity_calendar)


