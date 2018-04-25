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
from django.test import TestCase
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory

from base.business.entity import get_entity_calendar

from base.tests.factories.entity_calendar import EntityCalendarFactory
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_year import create_current_academic_year


class EntityTestCase(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()

    def test_get_entity_calendar_no_calendar(self):
        an_entity = EntityFactory()
        an_entity_version = EntityVersionFactory(entity=an_entity,
                                                 start_date=self.current_academic_year.start_date,
                                                 end_date=self.current_academic_year.end_date)
        self.assertIsNone(get_entity_calendar(an_entity_version, self.current_academic_year))

        an_academic_calendar = AcademicCalendarFactory(academic_year=self.current_academic_year,
                                                       start_date=self.current_academic_year.start_date,
                                                       end_date=self.current_academic_year.end_date,
                                                       reference=academic_calendar_type.EXAM_ENROLLMENTS)
        EntityCalendarFactory(entity=an_entity,
                              academic_calendar=an_academic_calendar,
                              start_date=an_academic_calendar.start_date,
                              end_date=an_academic_calendar.end_date)
        self.assertIsNone(get_entity_calendar(an_entity_version, self.current_academic_year))

    def test_get_entity_calendar_with_entity_calendar(self):
        an_entity = EntityFactory()
        an_entity_version = EntityVersionFactory(entity=an_entity,
                                                 start_date=self.current_academic_year.start_date,
                                                 end_date=self.current_academic_year.end_date)

        an_academic_calendar = AcademicCalendarFactory(academic_year=self.current_academic_year,
                                                       start_date=self.current_academic_year.start_date,
                                                       end_date=self.current_academic_year.end_date,
                                                       reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        an_entity_calendar = EntityCalendarFactory(entity=an_entity,
                                                   academic_calendar=an_academic_calendar,
                                                   start_date=an_academic_calendar.start_date,
                                                   end_date=an_academic_calendar.end_date)
        self.assertEqual(get_entity_calendar(an_entity_version, self.current_academic_year), an_entity_calendar)

    def test_get_entity_calendar_with_parent_entity_calendar(self):
        an_entity_parent = EntityFactory()
        EntityVersionFactory(entity=an_entity_parent,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date)
        an_entity_child = EntityFactory()
        an_child_entity_version = EntityVersionFactory(entity=an_entity_child,
                                                       start_date=self.current_academic_year.start_date,
                                                       end_date=self.current_academic_year.end_date,
                                                       parent=an_entity_parent)

        an_academic_calendar = AcademicCalendarFactory(academic_year=self.current_academic_year,
                                                       start_date=self.current_academic_year.start_date,
                                                       end_date=self.current_academic_year.end_date,
                                                       reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        an_parent_entity_calendar = EntityCalendarFactory(entity=an_entity_parent,
                                                          academic_calendar=an_academic_calendar,
                                                          start_date=an_academic_calendar.start_date,
                                                          end_date=an_academic_calendar.end_date)
        self.assertEqual(get_entity_calendar(an_child_entity_version, self.current_academic_year),
                         an_parent_entity_calendar)
