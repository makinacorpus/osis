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
from django.db import models
from django.utils.translation import ugettext_lazy as _

from attribution.models.attribution_new import AttributionNew
from base.models import learning_unit_year
from base.models.enums import learning_unit_year_subtypes, learning_container_year_types
from base.models.enums import vacant_declaration_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LearningContainerYearAdmin(SerializableModelAdmin):
    list_display = ('learning_container', 'academic_year', 'container_type', 'acronym', 'common_title')
    fieldsets = ((None, {'fields': ('academic_year', 'learning_container',  'container_type', 'acronym', 'common_title',
                                    'common_title_english', 'language', 'campus', 'is_vacant',
                                    'type_declaration_vacant', 'team', 'in_charge')}),)
    search_fields = ['acronym']
    raw_id_fields = ('learning_container', 'campus', )
    list_filter = ('academic_year', 'in_charge', 'is_vacant',)


class LearningContainerYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.ForeignKey('AcademicYear')
    learning_container = models.ForeignKey('LearningContainer')
    container_type = models.CharField(max_length=20, verbose_name=_('type'),
                                      choices=learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES)
    common_title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('common_official_title'))
    common_title_english = models.CharField(max_length=250, blank=True, null=True,
                                            verbose_name=_('common_official_english_title'))
    acronym = models.CharField(max_length=10)
    changed = models.DateTimeField(null=True, auto_now=True)
    language = models.ForeignKey('reference.Language', null=True, verbose_name=_('language'))
    campus = models.ForeignKey('Campus', null=True)
    team = models.BooleanField(default=False)
    is_vacant = models.BooleanField(default=False)
    type_declaration_vacant = models.CharField(max_length=100, blank=True, null=True,
                                               choices=vacant_declaration_type.DECLARATION_TYPE)
    in_charge = models.BooleanField(default=False)

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.common_title)

    class Meta:
        unique_together = ("learning_container", "academic_year",)
        permissions = (
            ("can_access_learningcontaineryear", "Can access learning container year"),
        )

    def get_partims_related(self):
        return learning_unit_year.search(learning_container_year_id=self,
                                         subtype=learning_unit_year_subtypes.PARTIM).order_by('acronym')

    def get_attributions(self):
        return AttributionNew.objects.filter(learning_container_year=self).select_related('tutor')


def find_by_id(learning_container_year_id):
    return LearningContainerYear.objects.get(pk=learning_container_year_id)


def search(an_academic_year=None, a_learning_container=None):
    queryset = LearningContainerYear.objects

    if an_academic_year:
        queryset = queryset.filter(academic_year=an_academic_year)
    if a_learning_container:
        queryset = queryset.filter(learning_container=a_learning_container)

    return queryset
