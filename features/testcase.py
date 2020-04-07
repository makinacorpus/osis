# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from behave_django.testcase import BehaviorDrivenTestCase
from django.utils.translation import gettext_lazy as _

from assessments.views import upload_xls_utils
from base.models.enums import exam_enrollment_justification_type


class OsisTestCase(BehaviorDrivenTestCase):
    def _fixture_teardown(self):
        pass

    def _flush_db(self):
        super()._fixture_teardown()

    def assertScoresEqual(self, page_results: list, scores_expected: list):
        for result, score in zip(page_results, scores_expected):
            if score.isdecimal():
                self.assertEqual(result.score.text, score)
                self.assertEqual(result.justification.text, "-")

            elif score in upload_xls_utils.AUTHORIZED_JUSTIFICATION_ALIASES:
                self.assertEqual(
                    result.score.text,
                    "-"
                )
                justification_value = get_enum_value(
                    exam_enrollment_justification_type.JUSTIFICATION_TYPES,
                    upload_xls_utils.AUTHORIZED_JUSTIFICATION_ALIASES[score]
                )
                self.assertEqual(
                    result.justification.text,
                    _(justification_value)
                )


def get_enum_value(enum, key):
    return next(
        (v for k, v in enum if k == key),
        None
    )
