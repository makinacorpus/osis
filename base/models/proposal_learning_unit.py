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
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from base.models.enums import proposal_type, proposal_state
from base.models.osis_model_admin import OsisModelAdmin
from base.models import entity, entity_version


class ProposalLearningUnitAdmin(OsisModelAdmin):
    list_display = ('learning_unit_year', 'folder_id', 'entity', 'type', 'state')

    search_fields = ['folder_id', 'learning_unit_year__acronym']
    list_filter = ('type', 'state')
    raw_id_fields = ('learning_unit_year', 'author', 'entity')


class ProposalLearningUnit(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    author = models.ForeignKey('Person', null=True)
    date = models.DateTimeField(auto_now=True)
    learning_unit_year = models.OneToOneField('LearningUnitYear')
    type = models.CharField(max_length=50, choices=proposal_type.CHOICES, verbose_name=_("type"),
                            default=proposal_type.ProposalType.MODIFICATION.name)
    state = models.CharField(max_length=50, choices=proposal_state.CHOICES, verbose_name=_("state"),
                             default=proposal_state.ProposalState.FACULTY.name)
    initial_data = JSONField(default={})
    entity = models.ForeignKey('Entity')
    folder_id = models.PositiveIntegerField()

    class Meta:
        permissions = (
            # TODO: Remove this permissions : already exists with can_change_proposal_learning_unit
            ("can_edit_learning_unit_proposal", "Can edit learning unit proposal"),
        )

    def __str__(self):
        return "{} - {}".format(self.folder_id, self.learning_unit_year)

    @property
    def folder(self):
        last_entity = entity_version.get_last_version(self.entity)
        return "{}{}".format(last_entity.acronym if last_entity else '', str(self.folder_id))


def find_by_learning_unit_year(a_learning_unit_year):
    try:
        return ProposalLearningUnit.objects.get(learning_unit_year=a_learning_unit_year)
    except ProposalLearningUnit.DoesNotExist:
        return None


def find_by_learning_unit(a_learning_unit):
    try:
        return ProposalLearningUnit.objects.get(learning_unit_year__learning_unit=a_learning_unit)
    except ObjectDoesNotExist:
        return None


def search(academic_year_id=None, acronym=None, entity_folder_id=None, folder_id=None, proposal_type=None,
           proposal_state=None, learning_container_year_id=None, tutor=None, *args, **kwargs):

    queryset = ProposalLearningUnit.objects

    if academic_year_id:
        queryset = queryset.filter(learning_unit_year__academic_year=academic_year_id)

    if acronym:
        queryset = queryset.filter(learning_unit_year__acronym__icontains=acronym)

    if entity_folder_id:
        queryset = queryset.filter(entity_id=entity_folder_id)

    if folder_id:
        queryset = queryset.filter(folder_id=folder_id)

    if proposal_type:
        queryset = queryset.filter(type=proposal_type)

    if proposal_state:
        queryset = queryset.filter(state=proposal_state)

    if learning_container_year_id is not None:
        if isinstance(learning_container_year_id, list):
            queryset = queryset.filter(learning_unit_year__learning_container_year__in=learning_container_year_id)
        elif learning_container_year_id:
            queryset = queryset.filter(learning_unit_year__learning_container_year=learning_container_year_id)

    if tutor:
        filter_by_first_name = {_build_tutor_filter(name_type='first_name'): tutor}
        filter_by_last_name = {_build_tutor_filter(name_type='last_name'): tutor}
        queryset = queryset.filter(Q(**filter_by_first_name) | Q(**filter_by_last_name)).distinct()

    return queryset.select_related('learning_unit_year')


def _build_tutor_filter(name_type):
    return '__'.join(['learning_unit_year', 'learningunitcomponent', 'learning_component_year', 'attributionchargenew',
                      'attribution', 'tutor', 'person', name_type, 'icontains'])


def count_search_results(**kwargs):
    return search(**kwargs).count()


def find_distinct_folder_entities():
    entities = ProposalLearningUnit.objects.distinct('entity').values_list('entity__id', flat=True)
    return entity.Entity.objects.filter(pk__in=entities)
