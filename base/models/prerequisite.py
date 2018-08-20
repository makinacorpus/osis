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
#############################################################################
from django.db import models

from osis_common.models.osis_model_admin import OsisModelAdmin


class PrerequisiteAdmin(OsisModelAdmin):
    list_display = ('learning_unit_year', 'education_group_year', 'prerequisite')
    raw_id_fields = ('learning_unit_year', 'education_group_year')
    list_filter = ('education_group_year__academic_year',)
    search_fields = ['learning_unit_year__acronym', 'education_group_year__acronym',
                     'education_group_year__partial_acronym']


class Prerequisite(models.Model):
    learning_unit_year = models.ForeignKey("LearningUnitYear")
    education_group_year = models.ForeignKey("EducationGroupYear")
    prerequisite = models.CharField(null=True, blank=True, max_length=240)

    class Meta:
        unique_together = ('learning_unit_year', 'education_group_year')

    def __str__(self):
        return "{}{} : {}".format(self.education_group_year, self.learning_unit_year, self.prerequisite)