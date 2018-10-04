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
from django.utils.translation import ugettext_lazy as _

SECTOR = "SECTOR"
FACULTY = "FACULTY"
SCHOOL = "SCHOOL"
INSTITUTE = "INSTITUTE"
POLE = "POLE"
DOCTORAL_COMMISSION = "DOCTORAL_COMMISSION"
PLATFORM = "PLATFORM"
LOGISTICS_ENTITY = "LOGISTICS_ENTITY"


ENTITY_TYPES = (
    (SECTOR, _(SECTOR)),
    (FACULTY, _(FACULTY)),
    (SCHOOL, _(SCHOOL)),
    (INSTITUTE, _(INSTITUTE)),
    (POLE, _(POLE)),
    (DOCTORAL_COMMISSION, _(DOCTORAL_COMMISSION)),
    (PLATFORM, _(PLATFORM)),
    (LOGISTICS_ENTITY, _(LOGISTICS_ENTITY)),
)


PEDAGOGICAL_ENTITY_TYPES = (SECTOR, FACULTY, SCHOOL, DOCTORAL_COMMISSION)
