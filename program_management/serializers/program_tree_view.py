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
from django.urls import reverse

from base.utils.urls import reverse_with_get
from program_management.serializers.node_view import serialize_children
from program_management.ddd.business_types import *


def program_tree_view_serializer(tree: 'ProgramTree') -> dict:
    path = str(tree.root_node.pk)
    return {
        'text': '%(code)s - %(title)s' % {'code': tree.root_node.code, 'title': tree.root_node.title},
        'id': path,
        'icon': None,
        'children': serialize_children(
            children=tree.root_node.children,
            path=path,
            context={'root': tree.root_node}
        ),
        'a_attr': {
            'href': reverse('element_identification', args=[tree.root_node.year, tree.root_node.code]),
            'element_id': tree.root_node.pk,
            'element_type': tree.root_node.type.name,
            'element_code': tree.root_node.code,
            'element_year': tree.root_node.year,
            'paste_url': reverse_with_get('tree_paste_node', get={"path": str(tree.root_node.pk)}),
            'search_url': reverse_with_get(
                'quick_search_education_group',
                args=[tree.root_node.academic_year.year],
                get={"path": str(tree.root_node.pk)}
            ),
        }
    }
