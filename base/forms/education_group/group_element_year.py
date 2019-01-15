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
from django.utils.translation import gettext as _

from base.models.enums import education_group_categories
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear


class GroupElementYearForm(forms.ModelForm):
    class Meta:
        model = GroupElementYear
        fields = [
            "relative_credits",
            "is_mandatory",
            "block",
            "quadrimester_derogation",
            "link_type",
            "comment",
            "comment_english",
            "access_condition"
        ]
        widgets = {
            "comment": forms.Textarea(attrs={'rows': 5}),
            "comment_english": forms.Textarea(attrs={'rows': 5}),

        }

    def __init__(self, *args, parent=None, child_branch=None, child_leaf=None, **kwargs):
        super().__init__(*args, **kwargs)

        # No need to attach FK to an existing GroupElementYear
        if not self.instance.pk:
            self.instance.parent = parent
            self.instance.child_leaf = child_leaf
            self.instance.child_branch = child_branch

        if self.instance.parent:
            self._define_fields()

    def _define_fields(self):
        parent_type = self.instance.parent.education_group_type
        if self.instance.child_branch and not parent_type.authorized_parent_type.filter(
                child_type=self.instance.child_branch.education_group_type).exists():
            self.fields.pop("access_condition")
            self.fields["link_type"].initial = LinkTypes.REFERENCE.name

        elif self._is_education_group_year_a_minor_major_option_list_choice(self.instance.parent):
            self._keep_only_fields(["access_condition"])

        elif self.instance.parent.education_group_type.category == education_group_categories.TRAINING and \
                self._is_education_group_year_a_minor_major_option_list_choice(self.instance.child_branch):
            self._keep_only_fields(["block"])

        else:
            self.fields.pop("access_condition")

    def save(self, commit=True):
        obj = super().save(commit)
        if self._is_education_group_year_a_minor_major_option_list_choice(obj.parent):
            self._reorder_children_by_partial_acronym(obj.parent)
        return obj

    def clean_link_type(self):
        """ In the case of a reference link. We have to check if all referenced children of the child_branch can
        be attach to the parent.
        """
        data_cleaned = self.cleaned_data.get('link_type')

        if data_cleaned == LinkTypes.REFERENCE.name and self.instance.child_branch:
            parent_type = self.instance.parent.education_group_type

            for ref_child in self.instance.child_branch.children_without_leaf:
                if parent_type.authorized_parent_type.filter(child_type=ref_child).exists():
                    continue

                self.add_error('link_type', _(
                    "You are not allow to create a reference link between a %(parent_type)s and a %(child_type)s."
                ) % {
                   "parent_type": parent_type,
                   "child_type": ref_child.education_group_type,
                })

        return data_cleaned

    @staticmethod
    def _reorder_children_by_partial_acronym(parent):
        children = parent.children.order_by("child_branch__partial_acronym")

        for counter, child in enumerate(children):
            child.order = counter
            child.save()

    def _keep_only_fields(self, fields_to_keep):
        self.fields = {name: field for name, field in self.fields.items() if name in fields_to_keep}

    def _is_education_group_year_a_minor_major_option_list_choice(self, egy):
        return egy.is_minor_major_option_list_choice if egy else False
