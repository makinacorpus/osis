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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from base.business.institution import find_summary_course_submission_dates_for_entity_version
from base.models.entity_version import find_last_entity_version_by_learning_unit_year_id
from base.models.learning_unit_year import LearningUnitYear
from osis_common.utils.datetime import get_tzinfo, convert_date_to_datetime


def can_user_view_educational_information(user, learning_unit_year_id):
    return LearningUnitYear.objects.filter(pk=learning_unit_year_id, summary_locked=False,
                                           attribution__summary_responsible=True,
                                           attribution__tutor__person__user=user).exists()


def can_user_edit_educational_information(user, learning_unit_year_id):
    if not can_user_view_educational_information(user, learning_unit_year_id):
        return False

    submission_dates = find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id)
    if not submission_dates:
        return False

    now = datetime.datetime.now(tz=get_tzinfo())
    return convert_date_to_datetime(submission_dates["start_date"]) <= now <= \
        convert_date_to_datetime(submission_dates["end_date"])


def find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id):
    entity_version = find_last_entity_version_by_learning_unit_year_id(learning_unit_year_id)
    if entity_version is None:
        return {}

    return find_summary_course_submission_dates_for_entity_version(entity_version)
