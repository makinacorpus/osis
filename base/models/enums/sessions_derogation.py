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
from enum import Enum
from base.models.utils.utils import ChoiceEnum


class SessionsDerogationTypes(ChoiceEnum):
    SESSION_1 = "SESSION_1"
    SESSION_2 = "SESSION_2"
    SESSION_3 = "SESSION_3"

    SESSION_1_2 = "SESSION_1_2"
    SESSION_1_3 = "SESSION_1_3"
    SESSION_2_3 = "SESSION_2_3"

    SESSION_1_2_3 = "SESSION_1_2_3"

    SESSION_UNDEFINED = "SESSION_UNDEFINED"

    SESSION_PARTIAL_2_3 = "SESSION_PARTIAL_2_3"

