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
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.acronym_field import AcronymField, PartimAcronymField
from base.forms.utils.choice_field import add_blank
from base.models.campus import find_main_campuses
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.entity_version import find_main_entities_version, get_last_version
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.component_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2, ENTITY_TYPE_LIST, REQUIREMENT_ENTITIES
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES, \
    CONTAINER_TYPE_WITH_DEFAULT_COMPONENT
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_component import LearningUnitComponent
from base.models.learning_unit_year import LearningUnitYear

DEFAULT_ACRONYM_COMPONENT = {
    LECTURING: "CM1",
    PRACTICAL_EXERCISES: "TP1",
    None: "NT1"
}


def _get_default_components_type(component_type):
    """This function will return the default components type to create/update according to container type"""
    if component_type in CONTAINER_TYPE_WITH_DEFAULT_COMPONENT:
        return [LECTURING, PRACTICAL_EXERCISES]
    return [None]


def _create_learning_container_year_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES)


def _create_faculty_learning_container_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY)


class EntitiesVersionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.acronym


class LearningUnitModelForm(forms.ModelForm):

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.start_year = kwargs.pop('academic_year').year
        return super(LearningUnitModelForm, self).save(**kwargs)

    class Meta:
        model = LearningUnit
        fields = ('periodicity', 'faculty_remark', 'other_remark', )
        widgets = {
            'faculty_remark': forms.Textarea(attrs={'rows': '5'}),
            'other_remark': forms.Textarea(attrs={'rows': '5'})
        }


class LearningContainerModelForm(forms.ModelForm):
    class Meta:
        model = LearningContainer
        fields = ()


class LearningUnitYearModelForm(forms.ModelForm):
    def __init__(self, data, person, subtype, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

        if person.is_faculty_manager():
            self.fields.pop('internship_subtype')

        self.instance.subtype = subtype

        if subtype == learning_unit_year_subtypes.PARTIM:
            self.fields['acronym'] = PartimAcronymField()
            self.fields['specific_title'].label = _('official_title_proper_to_partim')
            self.fields['specific_title_english'].label = _('official_english_title_proper_to_partim')

        if kwargs.get('instance'):
            self.fields['academic_year'].disabled = True

    class Meta:
        model = LearningUnitYear
        fields = ('academic_year', 'acronym', 'specific_title', 'specific_title_english', 'credits',
                  'session', 'quadrimester', 'status', 'internship_subtype', 'attribution_procedure', )

        field_classes = {'acronym': AcronymField}

    # TODO :: Move assignment to self.instance from save into __init__
    # TODO :: Make these kwarg to args (learning_container_year, learning_unit, ... are required args)
    def save(self, **kwargs):
        self.instance.learning_container_year = kwargs.pop('learning_container_year')
        self.instance.learning_unit = kwargs.pop('learning_unit')
        entity_container_years = kwargs.pop('entity_container_years')
        instance = super().save(**kwargs)
        self._save_learning_components(entity_container_years, instance)
        return instance

    def _save_learning_components(self, entity_container_years, learning_unit_year):
        components_type = _get_default_components_type(self.instance.learning_container_year.container_type)
        for component_type in components_type:
            component, created = LearningComponentYear.objects.get_or_create(
                learningunitcomponent__learning_unit_year=learning_unit_year,
                type=component_type,
                defaults={
                    'acronym': DEFAULT_ACRONYM_COMPONENT[component_type],
                    'learning_container_year': learning_unit_year.learning_container_year
                }
            )
            self._save_learning_unit_component(component, component_type, learning_unit_year)
            self._save_entity_components_year(component, entity_container_years)

    @staticmethod
    def _save_learning_unit_component(component, component_type, learning_unit_year):
        return LearningUnitComponent.objects.get_or_create(learning_unit_year=learning_unit_year,
                                                           learning_component_year=component,
                                                           type=component_type)

    @staticmethod
    def _save_entity_components_year(component, entity_container_years):
        requirement_entity_containers = filter(lambda ec: ec.type in REQUIREMENT_ENTITIES, entity_container_years)
        for requirement_entity_container in requirement_entity_containers:
            EntityComponentYear.objects.get_or_create(entity_container_year=requirement_entity_container,
                                                      learning_component_year=component)


class LearningUnitYearPartimModelForm(LearningUnitYearModelForm):
    class Meta(LearningUnitYearModelForm.Meta):
        labels = {
            'specific_title': _('official_title_proper_to_partim'),
            'specific_title_english': _('official_english_title_proper_to_partim')
        }
        field_classes = {
            'acronym': PartimAcronymField
        }


class EntityContainerYearModelForm(forms.ModelForm):
    entity = EntitiesVersionChoiceField(find_main_entities_version())

    def __init__(self, *args, **kwargs):
        entity_type = kwargs.pop('entity_type')
        self.person = kwargs.pop('person')
        super().__init__(*args, **kwargs)

        self.instance.type = entity_type
        self._set_field_by_entity_type(entity_type)

        self.fields['entity'].label = _(entity_type.lower())

        if hasattr(self.instance, 'entity'):
            self.initial['entity'] = get_last_version(self.instance.entity)

    def _set_field_by_entity_type(self, entity_type):
        set_by_entity_type = {
            REQUIREMENT_ENTITY: self.set_requirement_entity,
            ALLOCATION_ENTITY: self.set_allocation_entity,
            ADDITIONAL_REQUIREMENT_ENTITY_1: self.set_additional_requirement_entity_1,
            ADDITIONAL_REQUIREMENT_ENTITY_2: self.set_additional_requirement_entity_2,
        }
        set_by_entity_type[entity_type]()

    def set_requirement_entity(self):
        field = self.fields['entity']
        field.queryset = self.person.find_main_entities_version
        field.widget.attrs = {
            'onchange': (
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_1", false);'
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", true);'
            ), 'id': 'id_requirement_entity'}

    def set_allocation_entity(self):
        field = self.fields['entity']
        field.widget.attrs = {'id': 'allocation_entity'}

    def set_additional_requirement_entity_1(self):
        field = self.fields['entity']
        field.required = False
        field.widget.attrs = {
            'onchange':
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", false)',
                'disable': 'disable',
                'id': 'id_additional_requirement_entity_1'
            }

    def set_additional_requirement_entity_2(self):
        field = self.fields['entity']
        field.required = False
        field.widget.attrs = {'disable': 'disable', 'id': 'id_additional_requirement_entity_2'}

    class Meta:
        model = EntityContainerYear
        fields = ['entity']

    def clean_entity(self):
        entity_version = self.cleaned_data['entity']
        return entity_version.entity if entity_version else None

    def save(self, **kwargs):
        if hasattr(self.instance, 'entity'):
            return super(EntityContainerYearModelForm, self).save(**kwargs)


class EntityContainerYearFormset(forms.BaseInlineFormSet):

    def save(self, **kwargs):
        self.instance = kwargs.pop('learning_container_year')
        return super().save(**kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        instance = kwargs.get('instance')
        if not instance:
            kwargs['entity_type'] = ENTITY_TYPE_LIST[index]
        return kwargs

    @property
    def changed_data(self):
        return [form.changed_data for form in self.forms]


EntityContainerFormset = inlineformset_factory(
    LearningContainerYear, EntityContainerYear, form=EntityContainerYearModelForm,
    formset=EntityContainerYearFormset, max_num=4, min_num=3, extra=4, can_delete=False
)


class LearningContainerYearModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        person = kwargs.pop('person')
        proposal = kwargs.pop('proposal', False)
        super().__init__(*args, **kwargs)

        self.fields['campus'].queryset = find_main_campuses()
        self.fields['container_type'].widget.attrs = {'onchange': 'showInternshipSubtype()'}

        if person.is_faculty_manager() and not proposal:
            self.fields["container_type"].choices = _create_faculty_learning_container_type_list()

        if self.initial.get('subtype') == learning_unit_year_subtypes.PARTIM:
            self.fields["container_type"].choices = _create_learning_container_year_type_list()

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.acronym = kwargs.pop('acronym')
        self.instance.academic_year = kwargs.pop('academic_year')
        return super().save(**kwargs)

    class Meta:
        model = LearningContainerYear
        fields = ('container_type', 'common_title', 'common_title_english', 'language', 'campus',
                  'type_declaration_vacant', 'team', 'is_vacant')
