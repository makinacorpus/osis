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
import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property

from base.models.enums import entity_type
from base.models.enums.entity_type import MAIN_ENTITY_TYPE
from base.models.enums.organization_type import MAIN
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from osis_common.utils.datetime import get_tzinfo


class EntityVersionAdmin(SerializableModelAdmin):
    list_display = ('id', 'entity', 'acronym', 'parent', 'title', 'entity_type', 'start_date', 'end_date',)
    search_fields = ['entity__id', 'entity__external_id', 'title', 'acronym', 'entity_type', 'start_date', 'end_date']
    raw_id_fields = ('entity', 'parent')
    readonly_fields = ('find_direct_children', 'count_direct_children', 'find_descendants', 'get_parent_version')


class EntityVersionQuerySet(models.QuerySet):
    def current(self, date):
        if date:
            return self.filter(Q(end_date__gte=date) | Q(end_date__isnull=True), start_date__lte=date, )
        else:
            return self

    def entity(self, entity):
        return self.filter(entity=entity)


class EntityVersion(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    entity = models.ForeignKey('Entity')
    title = models.CharField(db_index=True, max_length=255)
    acronym = models.CharField(db_index=True, max_length=20)
    entity_type = models.CharField(choices=entity_type.ENTITY_TYPES, max_length=50, db_index=True, blank=True,
                                   null=True)
    parent = models.ForeignKey('Entity', related_name='parent_of', blank=True, null=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True, blank=True, null=True)

    objects = EntityVersionQuerySet.as_manager()

    def __str__(self):
        return "{} ({} - {} - {} to {})".format(
            self.acronym,
            self.title,
            self.entity_type,
            self.start_date,
            self.end_date
        )

    def save(self, *args, **kwargs):
        if self.can_save_entity_version():
            super(EntityVersion, self).save()
        else:
            raise AttributeError('EntityVersion invalid parameters')

    def exists_now(self):
        now = datetime.datetime.now().date()
        return (not self.end_date) or (self.end_date and self.start_date < now < self.end_date)

    def can_save_entity_version(self):
        return self.count_entity_versions_same_entity_overlapping_dates() == 0 and \
               self.count_entity_versions_same_acronym_overlapping_dates() == 0 and \
               self.parent != self.entity

    def search_entity_versions_with_overlapping_dates(self):
        if self.end_date:
            qs = EntityVersion.objects.filter(
                Q(start_date__range=(self.start_date, self.end_date)) |
                Q(end_date__range=(self.start_date, self.end_date)) |
                (
                    Q(start_date__lte=self.start_date) & Q(end_date__gte=self.end_date)
                )
            )
        else:
            qs = EntityVersion.objects.filter(
                end_date__gte=self.start_date
            )

        return qs.exclude(id=self.id)

    def count_entity_versions_same_entity_overlapping_dates(self):
        return self.search_entity_versions_with_overlapping_dates().filter(entity=self.entity).count()

    def count_entity_versions_same_acronym_overlapping_dates(self):
        return self.search_entity_versions_with_overlapping_dates().filter(acronym=self.acronym).count()

    def _direct_children(self, date=None):
        if date is None:
            date = timezone.now().date()

        if self.__contains_given_date(date):
            qs = EntityVersion.objects.current(date).filter(parent=self.entity).select_related('entity')
        else:
            qs = EntityVersion.objects.none()

        return qs

    def find_direct_children(self, date=None):
        if not date:
            direct_children = self.children
        else:
            direct_children = self._direct_children(date)
        return direct_children

    def count_direct_children(self, date=None):
        return self.find_direct_children(date).count()

    @cached_property
    def descendants(self):
        return self.find_descendants()

    @cached_property
    def children(self):
        return self._direct_children()

    def find_descendants(self, date=None):
        descendants = []
        direct_children = self.find_direct_children(date)
        if len(direct_children) > 0:
            descendants.extend(direct_children)
            for child in direct_children:
                descendants.extend(child.find_descendants(date))

        return sorted(descendants, key=lambda an_entity: an_entity.acronym)

    def find_faculty_version(self, academic_yr):
        if self.entity_type == entity_type.FACULTY:
            return self
        # There is no faculty above the sector
        elif self.entity_type == entity_type.SECTOR:
            return None
        else:
            parent_entity_version = self._find_latest_version_by_parent(academic_yr.start_date)
            if parent_entity_version:
                return parent_entity_version.find_faculty_version(academic_yr)

    def _find_latest_version_by_parent(self, start_date):
        if not self.parent:
            return None

        # if a prefetch exist on the parent
        entity_versions = getattr(self.parent, 'entity_versions', None)
        if not entity_versions:
            return find_latest_version_by_entity(self.parent, start_date)

        for entity_version in entity_versions:
            if entity_version.__contains_given_date(start_date):
                return entity_version

    def get_parent_version(self, date=None):
        if date is None:
            date = timezone.now().date()

        if self.__contains_given_date(date):
            qs = EntityVersion.objects.current(date).entity(self.parent)
            try:
                return qs.get()
            except EntityVersion.DoesNotExist:
                return None

    def __contains_given_date(self, date):
        if self.start_date and self.end_date:
            return self.start_date <= date <= self.end_date
        elif self.start_date and not self.end_date:
            return self.start_date <= date
        else:
            return False

    def get_organogram_data(self, level):
        level += 1
        if level < 3:
            return {
                'id': self.id,
                'acronym': self.acronym,
                'children': [child.get_organogram_data(level) for child in self.children]
            }
        else:
            return {
                'id': self.id,
                'acronym': self.acronym,
                'children': []
            }


def find(acronym, date=None):
    if date is None:
        date = timezone.now()
    try:
        entity_version = EntityVersion.objects.get(acronym=acronym,
                                                   start_date__lte=date,
                                                   end_date__gte=date
                                                   )
    except EntityVersion.DoesNotExist:
        return None

    return entity_version


def find_latest_version(date):
    return EntityVersion.objects.current(date).select_related('entity').order_by('-start_date')


def get_last_version(entity, date=None):
    qs = EntityVersion.objects.current(date).entity(entity)

    return qs.latest('start_date')


def get_last_version_by_entity_id(entity_id):
    now = datetime.datetime.now(get_tzinfo())
    return EntityVersion.objects.current(now).filter(entity__id=entity_id).latest('start_date')


def get_by_entity_parent(entity_parent):
    if entity_parent is None:
        return None
    try:
        return EntityVersion.objects.entity(entity_parent).get()
    except EntityVersion.DoesNotExist:
        return None


def get_by_entity_and_date(entity, date):
    if date is None:
        date = timezone.now()
    try:
        entity_version = EntityVersion.objects.current(date).entity(entity)
    except EntityVersion.DoesNotExist:
        return None
    return entity_version


def search(**kwargs):
    queryset = EntityVersion.objects

    if 'entity' in kwargs:
        queryset = queryset.filter(entity__exact=kwargs['entity'])

    if 'title' in kwargs:
        queryset = queryset.filter(title__icontains=kwargs['title'])

    if 'acronym' in kwargs:
        queryset = queryset.filter(acronym__icontains=kwargs['acronym'])

    if 'entity_type' in kwargs:
        queryset = queryset.filter(entity_type__exact=kwargs['entity_type'])

    if 'start_date' in kwargs:
        queryset = queryset.filter(start_date__exact=kwargs['start_date'])

    if 'end_date' in kwargs:
        queryset = queryset.filter(end_date__exact=kwargs['end_date'])

    return queryset.select_related('parent')


def count(**kwargs):
    return search(**kwargs).count()


def search_entities(acronym=None, title=None, entity_type=None, with_entity=None):
    queryset = EntityVersion.objects
    if with_entity:
        queryset = queryset.select_related('entity__organization')

    if acronym:
        queryset = queryset.filter(acronym__icontains=acronym)
    if title:
        queryset = queryset.filter(title__icontains=title)
    if entity_type:
        queryset = queryset.filter(entity_type=entity_type)

    return queryset


def find_by_id(entity_version_id):
    if entity_version_id is None:
        return
    try:
        return EntityVersion.objects.get(pk=entity_version_id)
    except EntityVersion.DoesNotExist:
        return None


def count_identical_versions(same_entity, version):
    return count(entity=same_entity,
                 title=version.get('title'),
                 acronym=version.get('acronym'),
                 entity_type=version.get('entity_type'),
                 parent=version.get('parent'),
                 start_date=version.get('start_date'),
                 end_date=version.get('end_date')
                 )


def find_update_candidates_versions(entity, version):
    to_update_versions = search(entity=entity,
                                title=version.get('title'),
                                acronym=version.get('acronym'),
                                entity_type=version.get('entity_type'),
                                parent=version.get('parent'),
                                start_date=version.get('start_date')
                                )
    return [v for v in to_update_versions if not _match_dates(v.end_date, version.get('end_date'))]


def _match_dates(osis_date, esb_date):
    if osis_date is None:
        return esb_date is None
    else:
        return osis_date.strftime('%Y-%m-%d') == esb_date


def find_all_current_entities_version():
    now = datetime.datetime.now(get_tzinfo())
    return find_latest_version(date=now)


def build_current_entity_version_structure_in_memory(date=None):
    if date:
        all_current_entities_version = find_latest_version(date=date)
    else:
        all_current_entities_version = find_all_current_entities_version()
    entity_version_by_entity_id = _build_entity_version_by_entity_id(all_current_entities_version)
    direct_children_by_entity_version_id = _build_direct_children_by_entity_version_id(entity_version_by_entity_id)
    all_children_by_entity_version_id = _build_all_children_by_entity_version_id(direct_children_by_entity_version_id)

    entity_versions = {}
    for entity_version in all_current_entities_version:
        entity_versions[entity_version.entity_id] = {
            'entity_version_parent': entity_version_by_entity_id.get(entity_version.parent_id),
            'direct_children': direct_children_by_entity_version_id.get(entity_version.id, []),
            'all_children': all_children_by_entity_version_id.get(entity_version.id, []),
        }
    return entity_versions


def _build_entity_version_by_entity_id(versions):
    return {version.entity_id: version for version in versions}


def _build_direct_children_by_entity_version_id(entity_version_by_entity_id):
    direct_children_by_entity_version_id = {}
    for entity_version in entity_version_by_entity_id.values():
        entity_version_parent = entity_version_by_entity_id.get(entity_version.parent_id)
        entity_version_parent_id = entity_version_parent.id if entity_version_parent else None
        direct_children_by_entity_version_id.setdefault(entity_version_parent_id, []).append(entity_version)
    return direct_children_by_entity_version_id


def _build_all_children_by_entity_version_id(direct_children_by_entity_version_id):
    return {entity_version_id: _get_all_children(entity_version_id, direct_children_by_entity_version_id)
            for entity_version_id in direct_children_by_entity_version_id.keys()}


def _get_all_children(entity_version_id, direct_children_by_entity_version_id):
    all_children = []
    for entity_version in direct_children_by_entity_version_id.get(entity_version_id, []):
        all_children.extend(_get_all_children(entity_version.id, direct_children_by_entity_version_id))
        all_children.append(entity_version)
    return all_children


def find_main_entities_version():
    return find_all_current_entities_version().filter(
        entity_type__in=MAIN_ENTITY_TYPE, entity__organization__type=MAIN).order_by('acronym')


def find_latest_version_by_entity(entity, date):
    return EntityVersion.objects.current(date).entity(entity).select_related('entity', 'parent').first()


def find_last_entity_version_by_learning_unit_year_id(learning_unit_year_id):
    now = datetime.datetime.now(get_tzinfo())
    try:
        return EntityVersion.objects.current(now).\
            filter(entity__entitycontaineryear__learning_container_year__learningunityear__id=learning_unit_year_id). \
            latest('start_date')
    except EntityVersion.DoesNotExist:
        return None


def search_by_acronyms(entities):
    q = Q()
    for entity in entities:
        q |= Q(acronym__icontains=entity.acronym)
    return EntityVersion.objects.filter(q)
