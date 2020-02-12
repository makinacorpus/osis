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
from django import forms
from django.forms import BaseFormSet

from base.models.enums.link_type import LinkTypes
from program_management.ddd.domain import program_tree
from program_management.ddd.service import attach_node_service
from program_management.ddd.repositories import fetch_node


class AttachNodeFormSet(BaseFormSet):
    def save(self):
        instances = []
        for f in self:
            instances.append(f.save())
        return instances

    def get_form_kwargs(self, index):
        if self.form_kwargs:
            return self.form_kwargs[index]
        return {}


class AttachNodeForm(forms.Form):
    access_condition = forms.BooleanField(required=False)
    is_mandatory = forms.BooleanField(required=False)
    block = forms.CharField(required=False)
    link_type = forms.ChoiceField(choices=LinkTypes.choices(), required=False)
    comment = forms.CharField(widget=forms.widgets.Textarea, required=False)
    comment_english = forms.CharField(widget=forms.widgets.Textarea, required=False)

    def __init__(self, tree: program_tree.ProgramTree, to_path: str, node_id: int, node_type: str, **kwargs):
        self.tree = tree
        self.to_path = to_path
        self.node = fetch_node.fetch_by_type(node_type, node_id)
        super().__init__(**kwargs)

    def save(self):
        attach_node_service.attach_node(
            self.tree,
            self.node,
            self.to_path,
            **self.cleaned_data
        )
