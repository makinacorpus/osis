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
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from base.forms.education_group_pedagogy_edit import EducationGroupPedagogyEditForm
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType
from base.models.person import get_user_interface_language
from cms.enums import entity_name
from cms.models import translated_text_label
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from education_group.models.group_year import GroupYear
from education_group.views.group.common_read import Tab, GroupRead


class GroupUpdateGeneralInformation(GroupRead):
    template_name = 'education_group/blocks/modal/modal_pedagogy_edit_inner.html'
    active_tab = Tab.GENERAL_INFO

    def get_form_class(self):
        return EducationGroupPedagogyEditForm

    def post(self, request, *args, **kwargs):
        if not self.have_general_information_tab():
            return redirect(
                reverse('group_identification', kwargs=self.kwargs) + "?path={}".format(self.get_path())
            )
        form = self.get_form_class()(request.POST)
        node = self.get_object()
        entity = entity_name.get_offers_or_groups_entity_from_node(node)
        obj = self.get_object_reference()
        redirect_url = reverse('group_identification', kwargs=self.kwargs) + "?path={}".format(self.get_path())

        if form.is_valid():
            label = form.cleaned_data['label']

            text_label = TextLabel.objects.filter(label=label, entity=entity).first()

            record, created = TranslatedText.objects.get_or_create(reference=obj.pk,
                                                                   entity=entity,
                                                                   text_label=text_label,
                                                                   language='fr-be')
            record.text = form.cleaned_data['text_french']
            record.save()

            record, created = TranslatedText.objects.get_or_create(reference=obj.pk,
                                                                   entity=entity,
                                                                   text_label=text_label,
                                                                   language='en')
            record.text = form.cleaned_data['text_english']
            record.save()

            redirect_url += "#section_{label_name}".format(label_name=label)
        return redirect(redirect_url)

    def get_context_data(self, **kwargs):
        node = self.get_object()
        obj = self.get_object_reference()

        label_name = self.request.GET.get('label')

        initial_values = self.get_translated_texts(obj, node)

        context = {
            'education_group_year': obj,
            'label': label_name,
            'form': EducationGroupPedagogyEditForm(initial=initial_values),
            'group_to_parent': self.request.GET.get("group_to_parent") or '0',
            'translated_label': translated_text_label.get_label_translation(
                text_entity=entity_name.get_offers_or_groups_entity_from_node(node),
                label=label_name,
                language=get_user_interface_language(self.request.user)
            )
        }
        return {
            **super().get_context_data(**kwargs),
            **context
        }

    def get_translated_texts(self, obj, node):
        initial_values = {'label': self.request.GET.get('label')}
        entity = entity_name.get_offers_or_groups_entity_from_node(node)
        fr_text = TranslatedText.objects.filter(
            reference=str(obj.pk),
            text_label__label=initial_values['label'],
            text_label__entity=entity,
            entity=entity,
            language='fr-be'
        ).first()
        if fr_text:
            initial_values.update({'text_french': fr_text.text})
        en_text = TranslatedText.objects.filter(
            reference=str(obj.pk),
            text_label__label=initial_values['label'],
            text_label__entity=entity,
            entity=entity,
            language='en'
        ).first()
        if en_text:
            initial_values.update({'text_english': en_text.text})
        return initial_values

    def get_object_reference(self):
        node = self.get_object()
        if node.node_type.name in GroupType.get_names():
            return get_object_or_404(
                GroupYear,
                element__pk=node.pk
            )
        else:
            return get_object_or_404(
                EducationGroupYear,
                educationgroupversion__root_group__element__pk=node.pk
            )

    def get_success_url(self):
        node = self.get_object()
        return reverse('group_identification', args=[node.year, node.code]) + '?path={}'.format(self.get_path())
