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
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.mandate import MandateFactory
from base.tests.factories.mandatary import MandataryFactory
from base.models.enums import mandate_type as mandate_types
from base.models import mandatary


class MandataryTest(TestCase):

    def test_find_by_education_group_year(self):
        today = datetime.date.today()
        # academic year 1
        start_date_ay_1 = today.replace(year=today.year - 3)
        end_date_ay_1 = today.replace(year=today.year - 2)
        academic_year_1 = AcademicYearFactory.build(start_date=start_date_ay_1,
                                                    end_date=end_date_ay_1,
                                                    year=today.year - 3)
        academic_year_1.save()
        # academic year 1
        start_date_ay_2 = today.replace(year=today.year - 2)
        end_date_ay_2 = today.replace(year=today.year - 1)
        academic_year_2 = AcademicYearFactory.build(start_date=start_date_ay_2,
                                                    end_date=end_date_ay_2,
                                                    year=today.year - 2)
        academic_year_2.save()

        an_education_group = EducationGroupFactory()
        # education group year for acy 1
        education_group_year_acy1_1 = EducationGroupYearFactory(education_group=an_education_group,
                                                                academic_year=academic_year_1)
        education_group_year_acy1_2 = EducationGroupYearFactory(education_group=an_education_group,
                                                                academic_year=academic_year_1)
        # education group year for acy 2
        education_group_year_acy2_1 = EducationGroupYearFactory(education_group=an_education_group,
                                                                academic_year=academic_year_2)
        # mandates
        mandate_secretary = MandateFactory(education_group=an_education_group, function=mandate_types.SECRETARY)
        mandate_president = MandateFactory(education_group=an_education_group, function=mandate_types.PRESIDENT)

        # Mandataries during academic year 1 period
        mandatary_secretary_egy1 = MandataryFactory(mandate=mandate_secretary,
                                                    start_date=start_date_ay_1,
                                                    end_date=end_date_ay_1)
        mandatary_president_egy1 = MandataryFactory(mandate=mandate_president,
                                                    start_date=start_date_ay_1,
                                                    end_date=end_date_ay_1)

        # Mandataries during academic year 2 period
        mandatary_secretary_egy_2 = MandataryFactory(mandate=mandate_secretary,
                                                     start_date=start_date_ay_2,
                                                     end_date=end_date_ay_2)

        self.assertListEqual(list(mandatary.find_by_education_group_year(education_group_year_acy1_1)),
                             [mandatary_president_egy1, mandatary_secretary_egy1])

