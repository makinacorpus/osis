# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################

from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import node
from program_management.ddd.repositories import load_tree, persist_tree, node as node_repository
from program_management.ddd.service import detach_node_service


def paste_element_service(paste_command: command.PasteElementCommand) -> 'LinkIdentity':
    node_identity = node.NodeIdentity(code=paste_command.node_to_paste_code, year=paste_command.node_to_paste_year)
    commit = paste_command.commit
    path_to_detach = paste_command.path_where_to_detach
    tree = load_tree.load(paste_command.root_id)
    node_to_attach = node_repository.NodeRepository.get(node_identity)

    if path_to_detach:
        detach_command = command.DetachNodeCommand(path_where_to_detach=path_to_detach, commit=commit)
        detach_node_service.detach_node(detach_command)

    link_created = tree.paste_node(node_to_attach, paste_command)

    if commit:
        persist_tree.persist(tree)
    return link_created.entity_id
