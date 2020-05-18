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

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http import HttpResponse, QueryDict
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

from base.ddd.utils.validation_message import MessageLevel, BusinessValidationMessage
from base.models.enums.education_group_types import GroupType
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import GroupFactory, EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.utils.cache import ElementCache
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.business.group_element_years.management import EDUCATION_GROUP_YEAR
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree.attach import AttachNodeFormSet, AttachNodeForm
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory, \
    NodeGroupYearFactory


def form_valid_effect(formset: AttachNodeFormSet):
    for form in formset:
        form.cleaned_data = {}
    return True


class TestAttachNodeView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.person = PersonFactory()

    def setUp(self):
        self.tree = self.setUpTreeData()
        self.url = reverse("tree_attach_node", kwargs={'root_id': self.tree.root_node.pk})
        self.client.force_login(self.person.user)

        fetch_tree_patcher = mock.patch('program_management.ddd.repositories.load_tree.load', return_value=self.tree)
        fetch_tree_patcher.start()
        self.addCleanup(fetch_tree_patcher.stop)

        self.fetch_from_cache_patcher = mock.patch(
            'program_management.business.group_element_years.management.fetch_nodes_selected',
            return_value=[]
        )
        self.fetch_from_cache_patcher.start()
        self.addCleanup(self.fetch_from_cache_patcher.stop)

        self.get_form_class_patcher = mock.patch(
            'program_management.forms.tree.attach._get_form_class',
            return_value=AttachNodeForm
        )
        self.get_form_class_patcher.start()
        self.addCleanup(self.get_form_class_patcher.stop)

        permission_patcher = mock.patch.object(PermissionRequiredMixin, "has_permission")
        self.permission_mock = permission_patcher.start()
        self.permission_mock.return_value = True
        self.addCleanup(permission_patcher.stop)

    def setUpTreeData(self):
        """
           |BIR1BA
           |----LBIR150T (common-core)
                |---LBIR1110 (UE)
           |----LBIR101G (subgroup)
        """
        root_node = NodeEducationGroupYearFactory(code="BIR1BA")
        common_core = NodeEducationGroupYearFactory(code="LBIR150T")
        learning_unit_node = NodeLearningUnitYearFactory(code='LBIR1110')
        subgroup = NodeEducationGroupYearFactory(code="LBIR101G")

        common_core.add_child(learning_unit_node)
        root_node.add_child(common_core)
        root_node.add_child(subgroup)
        return ProgramTree(root_node)

    def test_get_method_when_no_data_selected_on_cache(self):
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[0].child.pk)])
        response = self.client.get(self.url, data={"path": path})
        self.assertEquals(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/attach_inner.html')

        msgs = [m.message for m in messages.get_messages(response.wsgi_request)]
        self.assertEqual(msgs, [_("Please cut or copy an item before attach it")])
        self.assertTrue(self.permission_mock.called)

    @mock.patch('program_management.business.group_element_years.management.fetch_nodes_selected')
    def test_get_method_when_education_group_year_element_is_selected(self, mock_cache_elems):
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        mock_cache_elems.return_value = [(subgroup_to_attach.node_id, subgroup_to_attach.node_type)]

        # To path :  BIR1BA ---> COMMON_CORE
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[0].child.pk)])
        response = self.client.get(self.url, data={"path": path})
        self.assertEquals(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/attach_inner.html')

        self.assertIn('formset', response.context, msg="Probably there are no item selected on cache")
        self.assertIsInstance(response.context['formset'], AttachNodeFormSet)
        self.assertEquals(len(response.context['formset'].forms), 1)
        self.assertIsInstance(response.context['formset'].forms[0], AttachNodeForm)

    @mock.patch('program_management.business.group_element_years.management.fetch_nodes_selected')
    def test_get_method_when_multiple_education_group_year_element_are_selected(self, mock_cache_elems):
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        subgroup_to_attach_2 = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP,)
        mock_cache_elems.return_value = [
            (subgroup_to_attach.node_id, subgroup_to_attach.node_type),
            (subgroup_to_attach_2.node_id, subgroup_to_attach_2.node_type)
        ]

        # To path :  BIR1BA ---> LBIR101G
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.get(self.url, data={"path": path})
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'tree/attach_inner.html')

        self.assertIn('formset', response.context, msg="Probably there are no item selected on cache")
        self.assertIsInstance(response.context['formset'], AttachNodeFormSet)
        self.assertEqual(len(response.context['formset'].forms), 2)

    @mock.patch('program_management.business.group_element_years.management.fetch_nodes_selected')
    @mock.patch('program_management.forms.tree.attach.AttachNodeFormSet.is_valid')
    def test_post_method_case_formset_invalid(self, mock_formset_is_valid, mock_cache_elems):
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP)
        mock_cache_elems.return_value = [(subgroup_to_attach.node_id, subgroup_to_attach.node_type)]
        mock_formset_is_valid.return_value = False

        # To path :  BIR1BA ---> LBIR101G
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        response = self.client.post(self.url + "?path=" + path)

        self.assertTemplateUsed(response, 'tree/attach_inner.html')
        self.assertIn('formset', response.context, msg="Probably there are no item selected on cache")
        self.assertIsInstance(response.context['formset'], AttachNodeFormSet)

    @mock.patch('program_management.ddd.service.attach_node_service.attach_node')
    @mock.patch.object(AttachNodeFormSet, 'is_valid', new=form_valid_effect)
    @mock.patch.object(AttachNodeForm, 'is_valid')
    @mock.patch('program_management.business.group_element_years.management.fetch_nodes_selected')
    def test_post_method_case_formset_valid(self, mock_cache_elems, mock_form_valid, mock_service):
        mock_form_valid.return_value = True
        mock_service.return_value = [BusinessValidationMessage('Success', MessageLevel.SUCCESS)]
        subgroup_to_attach = NodeGroupYearFactory(node_type=GroupType.SUB_GROUP,)
        mock_cache_elems.return_value = [(subgroup_to_attach.node_id, subgroup_to_attach.node_type)]

        # To path :  BIR1BA ---> LBIR101G
        path = "|".join([str(self.tree.root_node.pk), str(self.tree.root_node.children[1].child.pk)])
        self.client.post(self.url + "?path=" + path)

        self.assertTrue(
            mock_service.called,
            msg="View must call attach node service (and not another layer) "
                "because the 'attach node' action uses multiple domain objects"
        )


@override_flag('education_group_update', active=True)
class TestAttachCheckView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

        cls.url = reverse("check_education_group_attach", args=["12"])
        cls.path = "12|25|98"

    def setUp(self):
        self.client.force_login(self.person.user)

        patcher_fetch_nodes_selected = mock.patch(
            "program_management.business.group_element_years.management.fetch_nodes_selected"
        )
        mock_fetch_nodes_selected = patcher_fetch_nodes_selected.start()
        mock_fetch_nodes_selected.return_value = [(36, NodeType.EDUCATION_GROUP), (89, NodeType.EDUCATION_GROUP)]
        self.addCleanup(patcher_fetch_nodes_selected.stop)

        patcher_check_attach = mock.patch("program_management.ddd.service.attach_node_service.check_attach")
        self.mock_check_attach = patcher_check_attach.start()
        self.mock_check_attach.return_value = []
        self.addCleanup(patcher_check_attach.stop)

    def test_when_check_errors_then_should_display_those_errors(self):
        self.mock_check_attach.return_value = ["Not valid"]
        response = self.client.get(self.url, data={
            "id": [36, 89],
            "content_type": EDUCATION_GROUP_YEAR,
            "path": self.path
        })
        self.assertTemplateUsed(response, "tree/check_attach_inner.html")

        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Not valid", msgs)

    def test_when_check_errors_and_accept_json_header_then_should_return_those_errors_as_json(self):
        self.mock_check_attach.return_value = ["Not valid"]
        response = self.client.get(self.url, data={
            "id": [36, 89],
            "content_type": EDUCATION_GROUP_YEAR,
            "path": self.path
        }, HTTP_ACCEPT="application/json")

        self.assertEqual(
            response.json(),
            {"error_messages": ["Not valid"]}
        )

    def test_when_no_check_errors_and_accept_json_header_then_should_json_response_with_empty_errors_messages(self):
        response = self.client.get(self.url, data={
            "id": [36, 89],
            "content_type": EDUCATION_GROUP_YEAR,
            "path": self.path
        }, HTTP_ACCEPT="application/json")

        self.assertEqual(
            response.json(),
            {"error_messages": []}
        )

    def test_when_no_check_errors_then_should_redirect_to_view_attach_nodes(self):
        response = self.client.get(self.url, data={
            "id": [36, 89],
            "content_type": EDUCATION_GROUP_YEAR,
            "path": self.path
        })

        qd = QueryDict(mutable=True)
        qd.update({
            "content_type": EDUCATION_GROUP_YEAR,
            "path": self.path
        })
        qd.setlist("id", [36, 89])
        expected_url = reverse("tree_attach_node", args=[12]) + "?{}".format(qd.urlencode())
        self.assertRedirects(
            response,
            expected_url,
            fetch_redirect_response=False
        )


@override_flag('education_group_update', active=True)
class TestMoveGroupElementYearView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.next_academic_year = AcademicYearFactory(current=True)
        cls.root_egy = EducationGroupYearFactory(academic_year=cls.next_academic_year)
        cls.group_element_year = GroupElementYearFactory(parent__academic_year=cls.next_academic_year)
        cls.selected_egy = GroupFactory(
            academic_year=cls.next_academic_year
        )
        GroupElementYearFactory(parent=cls.root_egy, child_branch=cls.selected_egy)

        path_to_detach = "|".join([str(cls.group_element_year.parent.pk), str(cls.group_element_year.child.pk)])
        path_to_attach = "|".join([str(cls.root_egy.pk), str(cls.selected_egy.pk)])
        cls.url = reverse("group_element_year_move", args=[cls.root_egy.id])
        cls.url = "{}?path={}&path_to_detach={}".format(
            cls.url, path_to_attach, path_to_detach
        )

        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

        permission_patcher = mock.patch.object(User, "has_perms")
        self.permission_mock = permission_patcher.start()
        self.permission_mock.return_value = True
        self.addCleanup(permission_patcher.stop)

    def test_should_check_attach_and_detach_permission(self):
        self.client.get(self.url)
        self.permission_mock.assert_has_calls(
            [
                mock.call(("base.detach_educationgroup",), self.group_element_year.parent),
                mock.call(("base.attach_educationgroup",), self.selected_egy)
            ]

        )
        self.assertTrue(self.permission_mock.called)

    def test_move(self):
        AuthorizedRelationshipFactory(
            parent_type=self.selected_egy.education_group_type,
            child_type=self.group_element_year.child_branch.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        ElementCache(self.person.user).save_element_selected(
            self.group_element_year.child_branch,
            source_link_id=self.group_element_year.id
        )

        self.client.post(self.url, data={
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1',
            "link_type": LinkTypes.REFERENCE.name
        })

        self.assertFalse(GroupElementYear.objects.filter(id=self.group_element_year.id))
        self.assertTrue(
            GroupElementYear.objects.filter(parent=self.selected_egy, child_branch=self.group_element_year.child_branch)
        )
