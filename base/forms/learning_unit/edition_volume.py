##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import OrderedDict

from django import forms
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units import edition
from base.business.learning_units.edition import check_postponement_conflict_report_errors
from base.forms.utils.emptyfield import EmptyField
from base.models.enums import entity_container_year_link_type as entity_types
from base.models.enums.component_type import DEFAULT_ACRONYM_COMPONENT, COMPONENT_TYPES
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITIES
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_CANT_UPDATE_BY_FACULTY, \
    CONTAINER_TYPE_WITH_DEFAULT_COMPONENT
from base.models.learning_component_year import LearningComponentYear
from osis_common.forms.widgets import FloatFormatInput


class VolumeField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_digits=6, decimal_places=2, min_value=0, **kwargs)


class VolumeEditionForm(forms.Form):
    requirement_entity_key = 'volume_' + entity_types.REQUIREMENT_ENTITY.lower()
    additional_requirement_entity_1_key = 'volume_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1.lower()
    additional_requirement_entity_2_key = 'volume_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2.lower()

    opening_brackets_field = EmptyField(label='[')
    opening_parenthesis_field = EmptyField(label='(')
    volume_q1 = VolumeField(
        label=_('Q1'),
        help_text=_('Volume Q1'),
        widget=FloatFormatInput(render_value=True),
        required=False,
    )
    add_field = EmptyField(label='+')
    volume_q2 = VolumeField(
        label=_('Q2'),
        help_text=_('Volume Q2'),
        widget=FloatFormatInput(render_value=True),
        required=False,
    )
    closing_parenthesis_field = EmptyField(label=')')
    equal_field_1 = EmptyField(label='=')
    volume_total = VolumeField(
        label=_('Vol. annual'),
        help_text=_('The annual volume must be equal to the sum of the volumes Q1 and Q2'),
        widget=FloatFormatInput(render_value=True),
        required=False,
    )
    help_volume_total = "{} = {} + {}".format(_('Volume total annual'), _('Volume Q1'), _('Volume Q2'))
    closing_brackets_field = EmptyField(label=']')
    mult_field = EmptyField(label='*')
    planned_classes = forms.IntegerField(label=_('Planned classes'), help_text=_('Planned classes'), min_value=0,
                                         widget=forms.TextInput(), required=False)
    equal_field_2 = EmptyField(label='=')

    _post_errors = []
    _parent_data = {}
    _faculty_manager_fields = ['volume_q1', 'volume_q2']

    def __init__(self, *args, **kwargs):
        self.component = kwargs.pop('component')
        self.learning_unit_year = kwargs.pop('learning_unit_year')
        self.entities = kwargs.pop('entities', [])
        self.is_faculty_manager = kwargs.pop('is_faculty_manager', False)

        self.title = _(self.component.get_type_display()) + ' ' if self.component.type else self.component.acronym
        self.title_help = _(self.component.get_type_display()) + ' ' if self.component.type else ''
        self.title_help += self.component.acronym

        super().__init__(*args, **kwargs)
        help_volume_global = "{} = {} * {}".format(_('volume total global'),
                                                   _('Volume total annual'),
                                                   _('Planned classes'))

        # Append dynamic fields
        entities_to_add = [entity for entity in REQUIREMENT_ENTITIES if entity in self.entities]
        size_entities_to_add = len(entities_to_add)
        if size_entities_to_add > 1:
            self.fields["opening_brackets_entities_field"] = EmptyField(label='[')
        for i, key in enumerate(entities_to_add):
            entity = self.entities[key]
            self.fields["volume_" + key.lower()] = VolumeField(
                label=entity.acronym,
                help_text=entity.title,
                widget=FloatFormatInput(render_value=True),
                required=False
            )
            if i != len(entities_to_add) - 1:
                self.fields["add" + key.lower()] = EmptyField(label='+')
        if size_entities_to_add > 1:
            self.fields["closing_brackets_entities_field"] = EmptyField(label=']')

        if self.is_faculty_manager \
                and self.learning_unit_year.is_full() \
                and self.learning_unit_year.learning_container_year.container_type \
                in LEARNING_CONTAINER_YEAR_TYPES_CANT_UPDATE_BY_FACULTY:
            self._disable_central_manager_fields()

    def _disable_central_manager_fields(self):
        for key, field in self.fields.items():
            if key not in self._faculty_manager_fields:
                field.disabled = True

    def clean(self):
        """
        Prevent faculty users to a volume to 0 if there was a value other than 0.
        Also, prevent the faculty user from putting a volume if its value was 0.
        """
        cleaned_data = super().clean()

        input_names = {
            'volume_q1': 'volume_q1',
            'volume_q2': 'volume_q2',
            'volume_total': 'volume_total',
            'planned_classes': 'planned_classes',
            'volume_requirement_entity': 'volume_requirement_entity',
            'volume_additional_requirement_entity_1': 'volume_additional_requirement_entity_1',
            'volume_additional_requirement_entity_2': 'volume_additional_requirement_entity_2',
        }

        _check_volumes_edition(self, input_names)

        return cleaned_data

    def get_entity_fields(self):
        entity_keys = [self.requirement_entity_key, self.additional_requirement_entity_1_key,
                       self.additional_requirement_entity_2_key]
        return [self.fields[key] for key in entity_keys if key in self.fields]

    def save(self, postponement):
        if not self.changed_data:
            return None

        conflict_report = {}
        if postponement:
            conflict_report = edition.get_postponement_conflict_report(self.learning_unit_year)
            luy_to_update_list = conflict_report['luy_without_conflict']
        else:
            luy_to_update_list = [self.learning_unit_year]

        with transaction.atomic():
            for component in self._find_learning_components_year(luy_to_update_list):
                self._save(component)

        # Show conflict error if exists
        check_postponement_conflict_report_errors(conflict_report)

    def _save(self, component):
        component.hourly_volume_total_annual = self.cleaned_data['volume_total']
        component.hourly_volume_partial_q1 = self.cleaned_data['volume_q1']
        component.hourly_volume_partial_q2 = self.cleaned_data['volume_q2']
        component.planned_classes = self.cleaned_data['planned_classes']
        self._set_requirement_entities(component)
        return component.save()

    def _set_requirement_entities(self, component):
        updated_repartition_volumes = {}
        for entity_container_type in component.repartition_volumes.keys():
            repartition_volume = self.cleaned_data.get('volume_' + entity_container_type.lower())
            updated_repartition_volumes[entity_container_type] = repartition_volume

        component.set_repartition_volumes(updated_repartition_volumes)

    def _find_learning_components_year(self, luy_to_update_list):
        return [
            lcy
            for lcy in LearningComponentYear.objects.filter(
                learning_unit_year__in=luy_to_update_list)
            if lcy.type == self.component.type
        ]


class VolumeEditionBaseFormset(forms.BaseFormSet):

    def __init__(self, *args, **kwargs):
        self.learning_unit_year = kwargs.pop('learning_unit_year')
        self.components = list(self.learning_unit_year.components.keys())
        self.components_values = list(self.learning_unit_year.components.values())
        self.is_faculty_manager = kwargs.pop('is_faculty_manager')

        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['learning_unit_year'] = self.learning_unit_year
        kwargs['component'] = self.components[index]
        kwargs['initial'] = self._clean_component_keys(self.components_values[index])
        kwargs['entities'] = self.learning_unit_year.entities
        kwargs['is_faculty_manager'] = self.is_faculty_manager
        return kwargs

    @staticmethod
    def _clean_component_keys(component_dict):
        # Field's name must be in lowercase
        return {k.lower(): v for k, v in component_dict.items()}

    def save(self, postponement):
        for form in self.forms:
            form.save(postponement)


class VolumeEditionFormsetContainer:
    """
    Create and Manage a set of VolumeEditionFormsets
    """

    def __init__(self, request, learning_units, person):
        self.formsets = OrderedDict()
        self.learning_units = learning_units
        self.parent = self.learning_units[0]
        self.postponement = int(request.POST.get('postponement', 1))
        self.request = request

        self.is_faculty_manager = person.is_faculty_manager and not person.is_central_manager

        for learning_unit in learning_units:
            volume_edition_formset = formset_factory(
                form=VolumeEditionForm, formset=VolumeEditionBaseFormset, extra=len(learning_unit.components)
            )
            self.formsets[learning_unit] = volume_edition_formset(
                request.POST or None,
                learning_unit_year=learning_unit,
                prefix=learning_unit.acronym,
                is_faculty_manager=self.is_faculty_manager
            )

    def is_valid(self):
        if not self.request.POST:
            return False

        if not all([formset.is_valid() for formset in self.formsets.values()]):
            return False

        return True

    def save(self):
        for formset in self.formsets.values():
            formset.save(self.postponement)

    @property
    def errors(self):
        errors = {}
        for formset in self.formsets.values():
            errors.update(self._get_formset_errors(formset))
        return errors

    @staticmethod
    def _get_formset_errors(formset):
        errors = {}
        for i, form_errors in enumerate(formset.errors):
            for name, error in form_errors.items():
                errors["{}-{}-{}".format(formset.prefix, i, name)] = error
        return errors


class SimplifiedVolumeForm(forms.ModelForm):
    _learning_unit_year = None
    _entity_containers = []

    add_field = EmptyField(label="+")
    equal_field = EmptyField(label='=')

    def __init__(self, component_type, index, *args, is_faculty_manager=False, proposal=False, **kwargs):
        component_type = component_type
        self.is_faculty_manager = is_faculty_manager
        self.index = index
        self.proposal = proposal
        super().__init__(*args, **kwargs)
        self.label = component_type[1]
        self.instance.type = component_type[0]
        self.instance.acronym = DEFAULT_ACRONYM_COMPONENT[self.instance.type]

    class Meta:
        model = LearningComponentYear
        fields = (
            'hourly_volume_total_annual',
            'hourly_volume_partial_q1',
            'hourly_volume_partial_q2',
            'planned_classes',
            'repartition_volume_requirement_entity',
            'repartition_volume_additional_entity_1',
            'repartition_volume_additional_entity_2'
        )
        widgets = {
            'hourly_volume_total_annual': FloatFormatInput(
                attrs={'title': _("The annual volume must be equal to the sum of the volumes Q1 and Q2")},
                render_value=True
            ),
            'hourly_volume_partial_q1': FloatFormatInput(attrs={'title': _("Volume Q1")}, render_value=True),
            'hourly_volume_partial_q2': FloatFormatInput(attrs={'title': _("Volume Q2")}, render_value=True),
            'planned_classes': forms.TextInput(attrs={'title': _("Planned classes")}),
            'repartition_volume_requirement_entity': FloatFormatInput(render_value=True),
            'repartition_volume_additional_entity_1': FloatFormatInput(render_value=True),
            'repartition_volume_additional_entity_2': FloatFormatInput(render_value=True),
        }

    def clean(self):
        """
        Prevent faculty users to a volume to 0 if there was a value other than 0.
        Also, prevent the faculty user from putting a volume if its value was 0.
        """
        cleaned_data = super().clean()

        input_names = {
            'volume_q1': 'hourly_volume_partial_q1',
            'volume_q2': 'hourly_volume_partial_q2',
            'volume_total': 'hourly_volume_total_annual',
            'planned_classes': 'planned_classes',
            'volume_requirement_entity': 'repartition_volume_requirement_entity',
            'volume_additional_requirement_entity_1': 'repartition_volume_additional_entity_1',
            'volume_additional_requirement_entity_2': 'repartition_volume_additional_entity_2',
        }

        _check_volumes_edition(self, input_names)

        return cleaned_data

    def save(self, commit=True):
        if self.need_to_create_untyped_component():
            self.instance.acronym = DEFAULT_ACRONYM_COMPONENT[None]
            self.instance.type = None
            # In case of untyped component, we just need to create only 1 component (not more)
            if self.index != 0:
                return None

        self.instance.learning_unit_year = self._learning_unit_year
        self._assert_repartition_volumes_consistency()
        return super().save(commit)

    def _assert_repartition_volumes_consistency(self):
        """In case EntityContainerYear does not exist (or was removed), need to reset repartition volumes to None."""
        existing_entity_container_types = {ec.type for ec in self._entity_containers if ec}
        for entity_container_type in LearningComponentYear.repartition_volume_attrs_by_entity_container_type().keys():
            if entity_container_type not in existing_entity_container_types:
                self.instance.set_repartition_volume(entity_container_type, None)

    def need_to_create_untyped_component(self):
        container_type = self._learning_unit_year.learning_container_year.container_type
        return container_type not in CONTAINER_TYPE_WITH_DEFAULT_COMPONENT


class SimplifiedVolumeFormset(forms.BaseModelFormSet):
    def __init__(self, data, person, proposal=False, *args, **kwargs):
        self.is_faculty_manager = person.is_faculty_manager and not person.is_central_manager
        self.proposal = proposal
        super().__init__(data, *args, prefix="component", **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['component_type'] = COMPONENT_TYPES[index]
        kwargs['is_faculty_manager'] = self.is_faculty_manager
        kwargs['proposal'] = self.proposal
        kwargs['index'] = index
        return kwargs

    @property
    def fields(self):
        fields = OrderedDict()
        for form_instance in self.forms:
            fields.update({form_instance.add_prefix(name): field for name, field in form_instance.fields.items()})
        return fields

    @property
    def instances_data(self):
        data = {}
        zip_form_and_initial_forms = zip(self.forms, self.initial_forms)
        for form_instance, initial_form in zip_form_and_initial_forms:
            for col in ['hourly_volume_total_annual', 'hourly_volume_partial_q1', 'hourly_volume_partial_q2']:
                value = getattr(form_instance.instance, col, None) or getattr(initial_form.instance, col, None)
                data[_(form_instance.instance.type) + ' (' + self.label_fields[col].lower() + ')'] = value
        return data

    @property
    def label_fields(self):
        """ Return a dictionary with the label of all fields """
        data = {}
        for form_instance in self.forms:
            data.update({
                key: field.label for key, field in form_instance.fields.items()
            })
        return data

    def save_all_forms(self, learning_unit_year, entity_container_years, commit=True):
        for form in self.forms:
            form._learning_unit_year = learning_unit_year
            form._entity_containers = entity_container_years
            form.save()
        return super().save(commit)


SimplifiedVolumeManagementForm = modelformset_factory(
    model=LearningComponentYear,
    form=SimplifiedVolumeForm,
    formset=SimplifiedVolumeFormset,
    extra=2,
    max_num=2
)


def _check_volumes_edition(obj, input_names):
    raw_volume_q1 = obj.cleaned_data.get(input_names['volume_q1'])
    volume_q1 = raw_volume_q1 or 0
    raw_volume_q2 = obj.cleaned_data.get(input_names['volume_q2'])
    volume_q2 = raw_volume_q2 or 0
    volume_total = obj.cleaned_data.get(input_names['volume_total']) or 0
    planned_classes = obj.cleaned_data.get(input_names['planned_classes']) or 0
    raw_volume_requirement_entity = obj.cleaned_data.get(input_names['volume_requirement_entity'])
    volume_requirement_entity = raw_volume_requirement_entity or 0
    raw_volume_additional_requirement_entity_1 = obj.cleaned_data.get(
        input_names['volume_additional_requirement_entity_1'])
    volume_additional_requirement_entity_1 = raw_volume_additional_requirement_entity_1 or 0
    raw_volume_additional_requirement_entity_2 = obj.cleaned_data.get(
        input_names['volume_additional_requirement_entity_2'])
    volume_additional_requirement_entity_2 = raw_volume_additional_requirement_entity_2 or 0

    if raw_volume_q1 is not None or raw_volume_q2 is not None:
        if volume_total != volume_q1 + volume_q2:
            obj.add_error(input_names['volume_total'],
                          _('The annual volume must be equal to the sum of the volumes Q1 and Q2'))
            if raw_volume_q1 is not None:
                obj.add_error(input_names['volume_q1'], "")
            if raw_volume_q2 is not None:
                obj.add_error(input_names['volume_q2'], "")

    if planned_classes > 0 and volume_total == 0:
        obj.add_error(input_names['planned_classes'],
                      _('planned classes cannot be greather than 0 while volume is equal to 0'))
    if planned_classes == 0 and volume_total > 0:
        obj.add_error(input_names['planned_classes'],
                      _('planned classes cannot be 0 while volume is greater than 0'))

    if raw_volume_requirement_entity is not None or \
            raw_volume_additional_requirement_entity_1 is not None or \
            raw_volume_additional_requirement_entity_2 is not None:
        if volume_total * planned_classes != volume_requirement_entity + volume_additional_requirement_entity_1 + \
                volume_additional_requirement_entity_2:
            if raw_volume_additional_requirement_entity_1 is None and \
                    raw_volume_additional_requirement_entity_2 is None:
                obj.add_error(input_names['volume_requirement_entity'],
                              _('The volume of the entity must be equal to the global volume'))
            else:
                obj.add_error(input_names['volume_requirement_entity'],
                              _('The sum of the volumes of the entities must be equal to the global volume'))
                if raw_volume_additional_requirement_entity_1 is not None:
                    obj.add_error(input_names['volume_additional_requirement_entity_1'], '')
                if raw_volume_additional_requirement_entity_2 is not None:
                    obj.add_error(input_names['volume_additional_requirement_entity_2'], '')

    is_fac = None
    initial_volume_q1 = None
    initial_volume_q2 = None
    if isinstance(obj, VolumeEditionForm):
        is_fac = obj.is_faculty_manager
        initial_volume_q1 = obj.initial.get(input_names['volume_q1'])
        initial_volume_q2 = obj.initial.get(input_names['volume_q2'])

    if isinstance(obj, SimplifiedVolumeForm):
        is_fac = obj.is_faculty_manager and not obj.proposal
        initial_volume_q1 = obj.instance.hourly_volume_partial_q1
        initial_volume_q2 = obj.instance.hourly_volume_partial_q2

    if is_fac:
        if 0 in [initial_volume_q1, initial_volume_q2]:
            if 0 not in [raw_volume_q1, raw_volume_q2]:
                obj.add_error(input_names['volume_q1'], _("One of the partial volumes must have a value to 0."))
                obj.add_error(input_names['volume_q2'], _("One of the partial volumes must have a value to 0."))

        else:
            if volume_q1 == 0:
                obj.add_error(input_names['volume_q1'], _("The volume can not be set to 0."))
            if volume_q2 == 0:
                obj.add_error(input_names['volume_q2'], _("The volume can not be set to 0."))
