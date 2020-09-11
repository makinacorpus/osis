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
import copy

from django.test import SimpleTestCase

from education_group.ddd.domain.exception import MiniTrainingCopyConsistencyException
from education_group.ddd.validators._copy_check_mini_training_consistency import CheckMiniTrainingConsistencyValidator

from education_group.tests.factories.mini_training import MiniTrainingFactory


class TestCheckMiniTrainingConsistencyValidator(SimpleTestCase):
    def test_assert_raise_exception_when_fields_are_different(self):
        mini_training_from = MiniTrainingFactory()
        mini_training_to = MiniTrainingFactory()

        validator = CheckMiniTrainingConsistencyValidator(mini_training_from, mini_training_to)
        with self.assertRaises(MiniTrainingCopyConsistencyException):
            validator.validate()

    def test_assert_return_true_when_identical(self):
        mini_training_from = MiniTrainingFactory()
        mini_training_to = copy.deepcopy(mini_training_from)

        validator = CheckMiniTrainingConsistencyValidator(mini_training_from, mini_training_to)
        self.assertTrue(validator.validate())
