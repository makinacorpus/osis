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
import mock
from django.test import TestCase

from program_management.ddd import command
from program_management.ddd.domain import exception, program_tree_version
from program_management.ddd.service.write import delete_standard_program_tree_version_service


class TestDeleteStandardProgramTreeVersion(TestCase):
    @mock.patch("program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository", autospec=True)
    def test_delete_program_tree_versions(self, mock_program_tree_version_repository):
        mock_program_tree_version_repository.delete.side_effect = [
            None,
            None,
            exception.ProgramTreeVersionNotFoundException
        ]

        delete_command = command.DeleteProgramTreeVersionCommand(
            offer_acronym='Acronym',
            version_name='',
            is_transition=False,
            from_year=2018)
        result = delete_standard_program_tree_version_service.delete_standard_program_tree_version(delete_command)

        self.assertListEqual(
            [
                program_tree_version.ProgramTreeVersionIdentity(
                    offer_acronym='Acronym',
                    year=2018,
                    version_name='',
                    is_transition=False
                ),
                program_tree_version.ProgramTreeVersionIdentity(
                    offer_acronym='Acronym',
                    year=2019,
                    version_name='',
                    is_transition=False
                )
            ],
            result
        )
        self.assertEqual(3, mock_program_tree_version_repository.delete.call_count)
