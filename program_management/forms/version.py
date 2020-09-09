##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict

from django import forms
from django.contrib.auth.models import User
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from base.business.event_perms import EventPermEducationGroupEdition
from base.forms.common import ValidationRuleMixin
from base.forms.utils.choice_field import BLANK_CHOICE
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from education_group.forms import fields
from education_group.templatetags.academic_year_display import display_as_academic_year
from program_management.ddd.command import GetEndPostponementYearCommand
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.read import get_end_postponement_year_service
from rules_management.enums import MINI_TRAINING_PGRM_ENCODING_PERIOD, MINI_TRAINING_DAILY_MANAGEMENT, \
    TRAINING_PGRM_ENCODING_PERIOD, TRAINING_DAILY_MANAGEMENT
from rules_management.mixins import PermissionFieldMixin


class SpecificVersionForm(forms.Form):
    version_name = forms.CharField(
        max_length=15,
        required=True,
        label=_('Acronym of version'),
        widget=TextInput(
            attrs={'onchange': 'validate_version_name()', 'style': "text-transform: uppercase;"}
        ),
    )
    title = forms.CharField(
        max_length=100,
        required=False,
        label=_('Full title of the french version'),
    )
    title_english = forms.CharField(
        max_length=100,
        required=False,
        label=_('Full title of the english version'),
    )
    end_year = forms.ChoiceField(
        required=False,
        label=_('This version exists until'),
    )

    def __init__(
            self,
            tree_version_identity: 'ProgramTreeVersionIdentity',
            node_identity: 'NodeIdentity',
            *args,
            **kwargs
    ):
        self.tree_version_identity = tree_version_identity
        self.node_identity = node_identity
        super().__init__(*args, **kwargs)

        self.__init_academic_year_choices()

    def __init_academic_year_choices(self):
        max_year = get_end_postponement_year_service.calculate_program_tree_end_postponement(
            GetEndPostponementYearCommand(code=self.node_identity.code, year=self.node_identity.year)
        )
        choices_years = [
            (year, display_as_academic_year(year))
            for year in range(self.tree_version_identity.year, max_year + 1)
        ]

        if not ProgramTreeVersionRepository.get(self.tree_version_identity).end_year_of_existence:
            choices_years += BLANK_CHOICE

        self.fields["end_year"].choices = choices_years
        if not self.fields["end_year"].initial:
            self.fields["end_year"].initial = choices_years[-1]

    def clean_end_year(self):
        end_year = self.cleaned_data["end_year"]
        return int(end_year) if end_year else None

    def clean_version_name(self):
        return self.cleaned_data['version_name'].upper()


class UpdateTrainingVersionForm(ValidationRuleMixin, PermissionFieldMixin, SpecificVersionForm):
    # panel_informations_form.html
    code = forms.CharField(label=_("Code"), disabled=True, required=False)
    category = forms.CharField(label=_("Category"), disabled=True, required=False)
    type = forms.CharField(label=_("Type of training"), disabled=True, required=False)
    active = forms.CharField(label=_("Status"), disabled=True, required=False)
    schedule_type = forms.CharField(label=_("Schedule type"), disabled=True, required=False)
    credits = fields.CreditField()
    constraint_type = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ConstraintTypeEnum.choices()),
        label=_("Type of constraint"),
        required=False,
    )
    min_constraint = forms.IntegerField(
        label=_("minimum constraint").capitalize(),
        required=False,
        widget=forms.TextInput
    )
    max_constraint = forms.IntegerField(
        label=_("maximum constraint").capitalize(),
        required=False,
        widget=forms.TextInput
    )
    offer_title_fr = forms.CharField(label=_("Title in French"), required=False, disabled=True)
    offer_title_en = forms.CharField(label=_("Title in English"), required=False, disabled=True)
    offer_partial_title_fr = forms.CharField(label=_("Partial title in French"), required=False, disabled=True)
    offer_partial_title_en = forms.CharField(label=_("Partial title in English"), required=False, disabled=True)

    keywords = forms.CharField(label=_('Keywords'), required=False, disabled=True)

    # panel_academic_informations_form.html
    academic_type = forms.CharField(label=_("Academic type"), disabled=True, required=False)
    duration = forms.CharField(label=_("Duration"), disabled=True, required=False)
    duration_unit = forms.CharField(label=_("duration unit").capitalize(), disabled=True, required=False)
    internship_presence = forms.CharField(label=_("Internship"), disabled=True, required=False)
    is_enrollment_enabled = forms.BooleanField(
        initial=False, label=_('Enrollment enabled'), required=False, disabled=True
    )
    has_online_re_registration = forms.BooleanField(
        initial=True, label=_('Web re-registration'), required=False, disabled=True
    )
    has_partial_deliberation = forms.BooleanField(
        initial=False, label=_('Web re-registration'), required=False, disabled=True
    )
    has_admission_exam = forms.BooleanField(
        initial=False, label=_('Admission exam'), required=False, disabled=True
    )
    has_dissertation = forms.BooleanField(
        initial=False, label=_('dissertation').capitalize(), required=False, disabled=True
    )
    produce_university_certificate = forms.BooleanField(
        initial=False,
        label=_('University certificate'),
        required=False,
        disabled=True
    )

    decree_category = forms.CharField(label=_("Decree category"), disabled=True, required=False)
    rate_code = forms.CharField(label=_("Rate code"), disabled=True, required=False)
    main_language = forms.CharField(label=_("Primary language"), disabled=True, required=False)
    english_activities = forms.CharField(label=_("activities in English").capitalize(), disabled=True, required=False)
    other_language_activities = forms.CharField(label=_("Other languages activities"), disabled=True, required=False)
    main_domain = forms.CharField(label=_('main domain').capitalize(), disabled=True, required=False)
    secondary_domains = forms.CharField(label=_('secondary domains').title(), disabled=True, required=False)
    isced_domain = forms.CharField(label=_('ISCED domain'), disabled=True, required=False)
    internal_comment = forms.CharField(label=_("comment (internal)").capitalize(), disabled=True, required=False)

    # panel_entities_form.html
    management_entity = forms.CharField()
    administration_entity = forms.CharField(label=_("Administration entity"), disabled=True, required=False)
    academic_year = forms.CharField(label=_("Validity"), disabled=True, required=False)
    start_year = forms.CharField(label=_("Start academic year"), disabled=True, required=False)
    teaching_campus = fields.MainCampusChoiceField(
        queryset=None,
        label=_("Learning location"),
        to_field_name="name"
    )
    enrollment_campus = forms.CharField(label=_("Enrollment campus"), disabled=True, required=False)
    other_campus_activities = forms.CharField(label=_("Activities on other campus"), disabled=True, required=False)

    # panel_funding_form.html
    can_be_funded = forms.BooleanField(initial=False, label=_('Funding'), disabled=True, required=False)
    funding_direction = forms.CharField(label=_("Funding direction"), disabled=True, required=False)
    can_be_international_funded = forms.BooleanField(
        initial=False,
        label=_('Funding international cooperation CCD/CUD'),
        required=False,
        disabled=True
    )
    international_funding_orientation = forms.CharField(
        label=_("Funding international cooperation CCD/CUD direction"),
        disabled=True,
        required=False,
    )

    # panel_remarks_form.html
    remark_fr = forms.CharField(widget=forms.Textarea, label=_("Remark"), required=False)
    remark_english = forms.CharField(widget=forms.Textarea, label=_("remark in english").capitalize(), required=False)

    # HOPS panel
    ares_code = forms.CharField(label=_('ARES study code'), widget=forms.TextInput(), required=False, disabled=True)
    ares_graca = forms.CharField(label=_('ARES-GRACA'), widget=forms.TextInput(), required=False, disabled=True)
    ares_authorization = forms.CharField(
        label=_('ARES ability'), widget=forms.TextInput(), required=False, disabled=True
    )
    code_inter_cfb = forms.CharField(
        label=_('Code co-graduation inter CfB'), required=False, disabled=True
    )
    coefficient = forms.CharField(label=_('Co-graduation total coefficient'), required=False, disabled=True)

    # Diploma tab
    leads_to_diploma = forms.BooleanField(
        initial=False,
        label=_('Leads to diploma/certificate'),
        required=False,
        disabled=True
    )
    diploma_printing_title = forms.CharField(max_length=240, required=False, label=_('Diploma title'), disabled=True)
    professional_title = forms.CharField(max_length=320, required=False, label=_('Professionnal title'), disabled=True)
    certificate_aims = forms.CharField(required=False, label=_('certificate aims').capitalize(), disabled=True)

    def __init__(
            self,
            training_version_identity: 'ProgramTreeVersionIdentity',
            node_identity: 'NodeIdentity',
            training_type: TrainingType,
            user: User,
            **kwargs
    ):
        self.user = user
        self.training_type = training_type

        super().__init__(training_version_identity, node_identity, **kwargs)
        self.fields['version_name'].disabled = True
        self.__init_management_entity_field()

    def __init_management_entity_field(self):
        self.fields['management_entity'] = fields.ManagementEntitiesChoiceField(
            person=self.user.person,
            initial=None,
            disabled=self.fields['management_entity'].disabled,
        )

    # ValidationRuleMixin
    def field_reference(self, field_name: str) -> str:
        return '.'.join(["TrainingForm", self.training_type.name, field_name])

    # PermissionFieldMixin
    def get_context(self) -> str:
        is_edition_period_opened = EventPermEducationGroupEdition(raise_exception=False).is_open()
        return TRAINING_PGRM_ENCODING_PERIOD if is_edition_period_opened else TRAINING_DAILY_MANAGEMENT

    # PermissionFieldMixin
    def get_model_permission_filter_kwargs(self) -> Dict:
        return {'context': self.get_context()}


class UpdateMiniTrainingVersionForm(ValidationRuleMixin, PermissionFieldMixin, SpecificVersionForm):
    code = forms.CharField(label=_("Code"), disabled=True, required=False)
    category = forms.CharField(label=_("Category"), disabled=True, required=False)
    type = forms.CharField(label=_("Type of training"), disabled=True, required=False)
    status = forms.CharField(label=_("Status"), disabled=True, required=False)
    schedule_type = forms.CharField(label=_("Schedule type"), disabled=True, required=False)
    management_entity = forms.CharField()
    academic_year = forms.CharField(label=_("Validity"), disabled=True, required=False)
    start_year = forms.CharField(label=_("Start academic year"), disabled=True, required=False)
    teaching_campus = fields.MainCampusChoiceField(
        queryset=None,
        label=_("Learning location"),
        to_field_name="name"
    )
    credits = fields.CreditField()
    constraint_type = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ConstraintTypeEnum.choices()),
        label=_("Type of constraint"),
        required=False,
    )
    min_constraint = forms.IntegerField(
        label=_("minimum constraint").capitalize(),
        required=False,
        widget=forms.TextInput
    )
    max_constraint = forms.IntegerField(
        label=_("maximum constraint").capitalize(),
        required=False,
        widget=forms.TextInput
    )
    offer_title_fr = forms.CharField(label=_("Title in French"), required=False, disabled=True)
    offer_title_en = forms.CharField(label=_("Title in English"), required=False, disabled=True)
    keywords = forms.CharField(label=_('Keywords'), required=False, disabled=True)
    remark_fr = forms.CharField(widget=forms.Textarea, label=_("Remark"), required=False)
    remark_en = forms.CharField(widget=forms.Textarea, label=_("remark in english").capitalize(), required=False)

    def __init__(
            self,
            mini_training_version_identity: 'ProgramTreeVersionIdentity',
            node_identity: 'NodeIdentity',
            mini_training_type: MiniTrainingType,
            user: User,
            **kwargs
    ):
        self.user = user
        self.mini_training_type = mini_training_type

        super().__init__(mini_training_version_identity, node_identity, **kwargs)
        self.fields['version_name'].disabled = True
        self.__init_management_entity_field()

    def __init_management_entity_field(self):
        self.fields['management_entity'] = fields.ManagementEntitiesChoiceField(
            person=self.user.person,
            initial=None,
            disabled=self.fields['management_entity'].disabled,
        )

    # ValidationRuleMixin
    def field_reference(self, field_name: str) -> str:
        return '.'.join(["MiniTrainingForm", self.mini_training_type.name, field_name])

    # PermissionFieldMixin
    def get_context(self) -> str:
        is_edition_period_opened = EventPermEducationGroupEdition(raise_exception=False).is_open()
        return MINI_TRAINING_PGRM_ENCODING_PERIOD if is_edition_period_opened else MINI_TRAINING_DAILY_MANAGEMENT

    # PermissionFieldMixin
    def get_model_permission_filter_kwargs(self) -> Dict:
        return {'context': self.get_context()}
