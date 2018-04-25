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
from unittest import mock

from django.forms import model_to_dict
from django.test import TestCase
from django.utils import timezone
from base.models import academic_calendar
from base.models.academic_calendar import find_dates_for_current_academic_year
from base.models.enums import academic_calendar_type
from base.models.exceptions import StartDateHigherThanEndDateException
from base.signals.publisher import compute_all_scores_encodings_deadlines
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, AcademicYearFakerFactory, \
    create_current_academic_year


class AcademicCalendarTest(TestCase):

    def test_start_date_higher_than_end_date(self):
        yr = timezone.now().year
        an_academic_year = AcademicYearFactory(year=yr)
        an_academic_calendar = AcademicCalendarFactory.build(academic_year=an_academic_year,
                                                             title="An event",
                                                             start_date=datetime.date(yr, 3, 4),
                                                             end_date=datetime.date(yr, 3, 3))
        self.assertRaises(StartDateHigherThanEndDateException, an_academic_calendar.save)

    def test_find_by_id(self):
        an_academic_year = AcademicYearFactory()
        tmp_academic_calendar = AcademicCalendarFactory(academic_year=an_academic_year)
        db_academic_calendar = academic_calendar.find_by_id(tmp_academic_calendar.id)
        self.assertIsNotNone(db_academic_calendar)
        self.assertEqual(db_academic_calendar, tmp_academic_calendar)

    def test_find_highlight_academic_calendar(self):
        an_academic_year = AcademicYearFakerFactory(start_date=timezone.now() - datetime.timedelta(days=10),
                                                    end_date=timezone.now() + datetime.timedelta(days=10))

        tmp_academic_calendar_1 = AcademicCalendarFactory(academic_year=an_academic_year, title="First calendar event")

        tmp_academic_calendar_2 = AcademicCalendarFactory(academic_year=an_academic_year, title="Second calendar event")

        null_academic_calendar = AcademicCalendarFactory(academic_year=an_academic_year,
                                                         title="A third event which is null",
                                                         highlight_description=None)

        empty_academic_calendar = AcademicCalendarFactory(academic_year=an_academic_year,
                                                          title="A third event which is null",
                                                          highlight_title="")

        db_academic_calendars = list(academic_calendar.find_highlight_academic_calendar())
        self.assertIsNotNone(db_academic_calendars)
        self.assertCountEqual(db_academic_calendars, [tmp_academic_calendar_1, tmp_academic_calendar_2])

    def test_find_academic_calendar_by_academic_year(self):
        tmp_academic_year = AcademicYearFactory()
        tmp_academic_calendar = AcademicCalendarFactory(academic_year=tmp_academic_year)
        db_academic_calendar = list(academic_calendar.find_academic_calendar_by_academic_year
                                    ([tmp_academic_year][0]))[0]
        self.assertIsNotNone(db_academic_calendar)
        self.assertEqual(db_academic_calendar, tmp_academic_calendar)

    def test_find_academic_calendar_by_academic_year_with_dates(self):
        tmp_academic_year = AcademicYearFactory(year=timezone.now().year)
        tmp_academic_calendar = AcademicCalendarFactory(academic_year=tmp_academic_year)
        db_academic_calendar = list(academic_calendar.find_academic_calendar_by_academic_year_with_dates
                                    (tmp_academic_year.id))[0]
        self.assertIsNotNone(db_academic_calendar)
        self.assertEqual(db_academic_calendar, tmp_academic_calendar)

    def test_compute_deadline_is_called_case_academic_calendar_save(self):
        with mock.patch.object(compute_all_scores_encodings_deadlines, 'send') as mock_method:
            AcademicCalendarFactory()
            self.assertTrue(mock_method.called)

    def test_find_academic_calendar_no_mandatory_args_mentioned(self):
        self.assertIsNone(academic_calendar.find_academic_calendar(None, None, timezone.now()))
        an_academic_year = AcademicYearFactory(year=timezone.now().year)
        self.assertIsNone(academic_calendar.find_academic_calendar(an_academic_year, None, timezone.now()))
        self.assertIsNone(academic_calendar.find_academic_calendar(None, "EVENT_CALENDAR", timezone.now()))


class TestFindDatesForCurrentAcademicYear(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.current_academic_calendar = AcademicCalendarFactory(academic_year=create_current_academic_year(),
                                                                reference=academic_calendar_type.EXAM_ENROLLMENTS)

    def test_when_no_matching_reference(self):
        dates = find_dates_for_current_academic_year(academic_calendar_type.TEACHING_CHARGE_APPLICATION)
        self.assertFalse(dates)

    def test_when_matched(self):
        dates = find_dates_for_current_academic_year(academic_calendar_type.EXAM_ENROLLMENTS)
        self.assertEqual(dates,
                         model_to_dict(self.current_academic_calendar,
                                       fields=("start_date", "end_date")))
