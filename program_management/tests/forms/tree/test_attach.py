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
from unittest import mock

from django.test import SimpleTestCase

from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree.attach import AttachNodeForm
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestAttachNodeForm(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        root_node = NodeGroupYearFactory()
        cls.tree = ProgramTree(root_node)
        super().setUpClass()

    def _get_attach_node_form_instance(self, link_attributes=None):
        to_path = str(self.tree.root_node.pk)
        node_to_attach = NodeGroupYearFactory()

        return AttachNodeForm(
            self.tree,
            to_path,
            node_to_attach.node_id,
            node_to_attach.node_type,
            data=link_attributes
        )

    def test_ensure_form_contains_fields(self):
        form_instance = self._get_attach_node_form_instance()
        expected_fields = {'access_condition', 'is_mandatory', 'block', 'link_type', 'comment', 'comment_english'}
        self.assertFalse(set(form_instance.fields.keys()) - expected_fields, msg="Form must contains fields")

    def test_ensure_link_type_choice(self):
        form_instance = self._get_attach_node_form_instance({'link_type': 'invalid_link_type'})
        self.assertFalse(form_instance.is_valid())
        self.assertTrue(form_instance.errors['link_type'])

    @mock.patch('program_management.ddd.service.attach_node_service.attach_node', return_value=True)
    def test_ensure_form_save_method_call_attach_node_service(self, mock_attach_node_service):
        form_instance = self._get_attach_node_form_instance({'is_mandatory': True, 'comment': 'Commentaire'})
        self.assertTrue(form_instance.is_valid())
        form_instance.save()

        self.assertTrue(
            mock_attach_node_service.called,
            msg="Form must call attach node service because there are validation between two business objects"
        )
        mock_attach_node_service.assert_called_with(
            form_instance.tree,
            form_instance.node,
            form_instance.to_path,

            access_condition=False,
            block='',
            is_mandatory=True,
            comment='Commentaire',
            comment_english='',
            link_type='',
        )
