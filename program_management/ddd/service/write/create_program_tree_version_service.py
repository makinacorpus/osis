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
from typing import List

from program_management.ddd.business_types import *
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionBuilder, ProgramTreeVersionIdentity
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


def create_program_tree_version(
        command: 'CreateProgramTreeVersionCommand',
        identity_standard: 'ProgramTreeVersionIdentity'
) -> List[ProgramTreeVersionIdentity]:
    identities = []
    while command.year <= command.end_postponement:
        program_tree_version_standard = ProgramTreeVersionRepository().get(entity_id=identity_standard)
        new_program_tree_version = ProgramTreeVersionBuilder().build_from(program_tree_version_standard, command)
        ProgramTreeVersionRepository.create(program_tree_version=new_program_tree_version)
        command.year = command.year + 1
        identities.append(new_program_tree_version.entity_id)
    return identities


def create_news_program_tree_version(command: 'CreateProgramTreeVersionCommand') -> List[ProgramTreeVersionIdentity]:
    identity_standard = ProgramTreeVersionIdentity(
        offer_acronym=command.offer_acronym,
        year=command.year,
        version_name='',
        is_transition=command.is_transition
    )
    return create_program_tree_version(command, identity_standard)


def extend_program_tree_version(command: 'CreateProgramTreeVersionCommand') -> List[ProgramTreeVersionIdentity]:
    identity = ProgramTreeVersionIdentity(
        offer_acronym=command.offer_acronym,
        year=command.year,
        version_name=command.version_name,
        is_transition=command.is_transition
    )
    last_program_tree_version_existing = ProgramTreeVersionRepository().get_last_in_past(identity)
    identity_standard = ProgramTreeVersionIdentity(
        offer_acronym=command.offer_acronym,
        year=command.year,
        version_name='',
        is_transition=command.is_transition
    )
    command.year = last_program_tree_version_existing.entity_id.year+1
    return create_program_tree_version(command, identity_standard)
