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
import re

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from base.models import entity_container_year
from base.models.academic_year import current_academic_year, compute_max_academic_year_adjournment, AcademicYear
from base.models.enums import active_status, learning_container_year_types
from base.models.enums import learning_unit_year_subtypes, internship_subtypes, \
    learning_unit_year_session, entity_container_year_link_type, learning_unit_year_quadrimesters, attribution_procedure
from base.models.enums.learning_unit_periodicity import ANNUAL
from base.models.learning_unit import LEARNING_UNIT_ACRONYM_REGEX_ALL, REGEX_BY_SUBTYPE
from base.models.proposal_learning_unit import ProposalLearningUnit
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin

AUTHORIZED_REGEX_CHARS = "$*+.^"
REGEX_ACRONYM_CHARSET = "[A-Z0-9" + AUTHORIZED_REGEX_CHARS + "]+"
MINIMUM_CREDITS = 0.0
MAXIMUM_CREDITS = 500


def academic_year_validator(value):
    academic = AcademicYear.objects.get(pk=value)
    academic_year_max = compute_max_academic_year_adjournment()
    if academic.year > academic_year_max:
        raise ValidationError(_('learning_unit_creation_academic_year_max_error').format(academic_year_max))


class LearningUnitYearAdmin(SerializableModelAdmin):
    list_display = ('external_id', 'acronym', 'specific_title', 'academic_year', 'credits', 'changed', 'structure',
                    'status')
    fieldsets = ((None, {'fields': ('academic_year', 'learning_unit', 'learning_container_year', 'acronym',
                                    'specific_title', 'specific_title_english', 'subtype', 'credits', 'decimal_scores',
                                    'structure', 'internship_subtype', 'status', 'session',
                                    'quadrimester', 'attribution_procedure', 'summary_locked')}),)
    list_filter = ('academic_year', 'decimal_scores', 'summary_locked')
    raw_id_fields = ('learning_unit', 'learning_container_year', 'structure')
    search_fields = ['acronym', 'structure__acronym', 'external_id']


class LearningUnitYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.ForeignKey(AcademicYear,  verbose_name=_('academic_year'),
                                      validators=[academic_year_validator])
    learning_unit = models.ForeignKey('LearningUnit')
    learning_container_year = models.ForeignKey('LearningContainerYear', blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True, verbose_name=_('code'),
                               validators=[RegexValidator(LEARNING_UNIT_ACRONYM_REGEX_ALL)])
    specific_title = models.CharField(max_length=255, blank=True, null=True,
                                      verbose_name=_('official_title_proper_to_UE'))
    specific_title_english = models.CharField(max_length=250, blank=True, null=True,
                                              verbose_name=_('official_english_title_proper_to_UE'))
    subtype = models.CharField(max_length=50, choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
                               default=learning_unit_year_subtypes.FULL)
    credits = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                  validators=[MinValueValidator(MINIMUM_CREDITS), MaxValueValidator(MAXIMUM_CREDITS)])
    decimal_scores = models.BooleanField(default=False)
    structure = models.ForeignKey('Structure', blank=True, null=True)
    internship_subtype = models.CharField(max_length=250, blank=True, null=True,
                                          verbose_name=_('internship_subtype'),
                                          choices=internship_subtypes.INTERNSHIP_SUBTYPES)
    status = models.BooleanField(default=False, verbose_name=_('active_title'))
    session = models.CharField(max_length=50, blank=True, null=True,
                               choices=learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION)
    quadrimester = models.CharField(max_length=4, blank=True, null=True, verbose_name=_('quadrimester'),
                                    choices=learning_unit_year_quadrimesters.LEARNING_UNIT_YEAR_QUADRIMESTERS)
    attribution_procedure = models.CharField(max_length=20, blank=True, null=True,
                                             choices=attribution_procedure.ATTRIBUTION_PROCEDURES)
    summary_locked = models.BooleanField(default=False, verbose_name=_("summary_locked"))

    mobility_modality = models.CharField(max_length=250, verbose_name=_('Modalities specific to IN and OUT mobility'),
                                         blank=True, null=True)

    class Meta:
        unique_together = ('learning_unit', 'academic_year',)

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.acronym)

    @property
    def subdivision(self):
        if self.acronym and self.learning_container_year:
            return self.acronym.replace(self.learning_container_year.acronym, "")
        return None

    @property
    def parent(self):
        if self.subdivision and self.is_partim():
            return LearningUnitYear.objects.filter(
                subtype=learning_unit_year_subtypes.FULL,
                learning_container_year=self.learning_container_year,
            ).get()
        return None

    @property
    def same_container_learning_unit_years(self):
        return LearningUnitYear.objects.filter(
            learning_container_year=self.learning_container_year
        ).order_by('acronym')

    @cached_property
    def allocation_entity(self):
        return self.get_entity(entity_container_year_link_type.ALLOCATION_ENTITY)

    @cached_property
    def requirement_entity(self):
        return self.get_entity(entity_container_year_link_type.REQUIREMENT_ENTITY)

    @property
    def complete_title(self):
        complete_title = self.specific_title
        if self.learning_container_year:
            complete_title = ' '.join(filter(None, [self.learning_container_year.common_title, self.specific_title]))
        return complete_title

    @property
    def container_common_title(self):
        if self.learning_container_year:
            return self.learning_container_year.common_title
        return ''

    def get_partims_related(self):
        if self.is_full() and self.learning_container_year:
            return self.learning_container_year.get_partims_related()
        return LearningUnitYear.objects.none()

    def find_list_group_element_year(self):
        return self.child_leaf.filter(child_leaf=self).select_related('parent')

    def get_learning_unit_next_year(self):
        try:
            return LearningUnitYear.objects.get(learning_unit=self.learning_unit,
                                                academic_year__year=(self.academic_year.year + 1))
        except LearningUnitYear.DoesNotExist:
            return None

    @property
    def in_charge(self):
        return self.learning_container_year and self.learning_container_year.in_charge

    def is_in_proposal(self):
        return ProposalLearningUnit.objects.filter(learning_unit_year=self).exists()

    def find_gte_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gte=self.academic_year.year) \
            .order_by('academic_year__year')

    def find_gt_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gt=self.academic_year.year) \
            .order_by('academic_year__year')

    def is_past(self):
        return self.academic_year.year < current_academic_year().year

    def can_update_by_faculty_manager(self):
        result = False

        if not self.learning_container_year:
            return result

        current_year = current_academic_year().year
        year = self.academic_year.year

        if self.learning_unit.periodicity == ANNUAL and year <= current_year + 1:
            result = True
        elif self.learning_unit.periodicity != ANNUAL and year <= current_year + 2:
            result = True
        return result

    def is_full(self):
        return self.subtype == learning_unit_year_subtypes.FULL

    def is_partim(self):
        return self.subtype == learning_unit_year_subtypes.PARTIM

    def get_entity(self, entity_type):
        entity_container_yr = entity_container_year.search(link_type=entity_type,
                                                           learning_container_year=self.learning_container_year).get()
        return entity_container_yr.entity if entity_container_yr else None

    def clean(self):
        learning_unit_years = find_gte_year_acronym(self.academic_year, self.acronym)

        if getattr(self, 'learning_unit', None):
            learning_unit_years = learning_unit_years.exclude(learning_unit=self.learning_unit)

        self.clean_acronym(learning_unit_years)
        self.clean_internship_subtype()
        self.clean_status()
        self.clean_credits()

    def clean_internship_subtype(self):
        if getattr(self, 'learning_container_year', None):
            if (self.learning_container_year.container_type == learning_container_year_types.INTERNSHIP and
                    not self.internship_subtype):
                raise ValidationError({'internship_subtype': _('field_is_required')})

    def clean_acronym(self, learning_unit_years):
        if self.acronym in learning_unit_years.values_list('acronym', flat=True):
            raise ValidationError({'acronym': _('already_existing_acronym')})
        if not re.match(REGEX_BY_SUBTYPE[self.subtype], self.acronym):
            raise ValidationError({'acronym': _('invalid_acronym')})

    def clean_status(self):
        # If the parent is inactive, the partim can be only inactive
        if self.parent:
            if not self.parent.status and self.status:
                raise ValidationError({'status', _('The partim must be inactive because the parent is inactive')})

    def clean_credits(self):
        # TODO :: Create non null constraint in DB (how to manage external learning units with credits==Null?)
        if not self.credits:
            raise ValidationError({'credits': _('field_is_required')})
        if not self.parent:
            return
        if self.credits > self.parent.credits:
            raise ValidationError({'credits': _('partim_credits_gt_parent_credits')})
        elif self.credits == self.parent.credits:
            raise ValidationError({'credits':  _('partim_credits_equals_parent_credits')})


def get_by_id(learning_unit_year_id):
    return LearningUnitYear.objects.select_related('learning_container_year__learning_container') \
        .get(pk=learning_unit_year_id)


def find_by_acronym(acronym):
    return LearningUnitYear.objects.filter(acronym=acronym).select_related('learning_container_year')


def _is_regex(acronym):
    return set(AUTHORIZED_REGEX_CHARS).intersection(set(acronym))


def search(academic_year_id=None, acronym=None, learning_container_year_id=None, learning_unit=None,
           title=None, subtype=None, status=None, container_type=None, tutor=None,
           summary_responsible=None, requirement_entities=None, *args, **kwargs):
    queryset = LearningUnitYear.objects

    if academic_year_id:
        queryset = queryset.filter(academic_year=academic_year_id)

    if acronym:
        if _is_regex(acronym):
            queryset = queryset.filter(acronym__iregex=r"(" + acronym + ")")
        else:
            queryset = queryset.filter(acronym__icontains=acronym)

    if learning_container_year_id is not None:
        if isinstance(learning_container_year_id, list):
            queryset = queryset.filter(learning_container_year__in=learning_container_year_id)
        elif learning_container_year_id:
            queryset = queryset.filter(learning_container_year=learning_container_year_id)

    if requirement_entities:
        queryset = queryset.filter(
            learning_container_year__entitycontaineryear__entity__entityversion__in=requirement_entities,
            learning_container_year__entitycontaineryear__type=entity_container_year_link_type.REQUIREMENT_ENTITY)

    if learning_unit:
        queryset = queryset.filter(learning_unit=learning_unit)

    if title:
        queryset = queryset.\
            filter(Q(specific_title__icontains=title) | Q(learning_container_year__common_title__icontains=title))

    if subtype:
        queryset = queryset.filter(subtype=subtype)

    if status:
        queryset = queryset.filter(status=convert_status_bool(status))

    if container_type:
        queryset = queryset.filter(learning_container_year__container_type=container_type)

    if tutor:
        filter_by_first_name = {_build_tutor_filter(name_type='first_name'): tutor}
        filter_by_last_name = {_build_tutor_filter(name_type='last_name'): tutor}
        queryset = queryset.filter(Q(**filter_by_first_name) | Q(**filter_by_last_name)).distinct()

    if summary_responsible:
        queryset = find_summary_responsible_by_name(queryset, summary_responsible)

    return queryset.select_related('learning_container_year', 'academic_year')


def find_summary_responsible_by_name(queryset, name):
    for term in name.split():
        queryset = queryset.filter(
            Q(attribution__tutor__person__first_name__icontains=term) |
            Q(attribution__tutor__person__last_name__icontains=term)
        )

    return queryset.filter(attribution__summary_responsible=True).distinct()


def _build_tutor_filter(name_type):
    return '__'.join(['learningunitcomponent', 'learning_component_year', 'attributionchargenew', 'attribution',
                      'tutor', 'person', name_type, 'icontains'])


def convert_status_bool(status):
    if status in (active_status.ACTIVE, active_status.INACTIVE):
        boolean = status == active_status.ACTIVE
    else:
        boolean = status
    return boolean


def count_search_results(**kwargs):
    return search(**kwargs).count()


def find_gte_year_acronym(academic_yr, acronym):
    return LearningUnitYear.objects.filter(academic_year__year__gte=academic_yr.year,
                                           acronym__iexact=acronym)


def find_lt_year_acronym(academic_yr, acronym):
    return LearningUnitYear.objects.filter(academic_year__year__lt=academic_yr.year,
                                           acronym__iexact=acronym).order_by('academic_year')


def check_if_acronym_regex_is_valid(acronym):
    if isinstance(acronym, str):
        return re.fullmatch(REGEX_ACRONYM_CHARSET, acronym.upper())


def find_max_credits_of_related_partims(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().aggregate(max_credits=models.Max("credits"))["max_credits"]


def find_by_learning_unit(a_learning_unit):
    return search(learning_unit=a_learning_unit)


def find_by_entities(entities):
    return LearningUnitYear.objects.filter(learning_container_year__entitycontaineryear__entity__in=entities)


def find_latest_by_learning_unit(a_learning_unit):
    return search(learning_unit=a_learning_unit).order_by('academic_year').last()
