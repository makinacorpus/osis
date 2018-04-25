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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _
from base.templatetags.learning_unit import get_difference_css, has_proposal
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory


LABEL_VALUE_BEFORE_PROPROSAL = _('value_before_proposal')


class LearningUnitTagTest(TestCase):

    def test_get_difference_css(self):
        key_parameter_1 = 'parameter1'
        tooltip_parameter1 = 'tooltip1'

        differences = {key_parameter_1: tooltip_parameter1,
                       'parameter2': 'tooltip2'}

        self.assertEqual(get_difference_css(differences, key_parameter_1),
                         " data-toggle=tooltip title='{} : {}' class={} ".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                                 tooltip_parameter1,
                                                                                 "proposal_value"))

    def test_get_no_differences_css(self):
        differences = {'parameter1': 'tooltip1'}
        self.assertIsNone(get_difference_css(differences, 'parameter_10'))

    def test_has_proposal(self):
        luy = LearningUnitYearFactory()
        self.assertFalse(has_proposal(luy))
        ProposalLearningUnitFactory(learning_unit_year=luy)
        self.assertTrue(has_proposal(luy))
