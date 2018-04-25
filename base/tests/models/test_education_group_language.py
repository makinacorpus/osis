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
from base.models.education_group_language import find_by_education_group_year
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_language import EducationGroupLanguageFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from reference.tests.factories.language import LanguageFactory


class EducationGroupLanguageTest(TestCase):
    def setUp(self):
        academic_year = AcademicYearFactory()
        self.education_group_year = EducationGroupYearFactory(academic_year=academic_year)
        self.language = LanguageFactory()
        self.education_group_language_1 = EducationGroupLanguageFactory(education_group_year=self.education_group_year,
                                                                        language=self.language)
        self.education_group_language_2 = EducationGroupLanguageFactory(education_group_year=self.education_group_year,
                                                                        language=self.language)

    def test_return_str_format(self):
        self.assertEqual(self.education_group_language_1.__str__(), str(self.education_group_language_1.id))

    def test_find_by_education_group_year(self):
        education_group_year = find_by_education_group_year(self.education_group_year.id)
        self.assertEqual(education_group_year.count(), 2)
