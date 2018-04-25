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
import factory
import factory.fuzzy
import string
import datetime
import operator

from base.tests.factories.entity import EntityFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.models.enums import proposal_state, proposal_type
from osis_common.utils.datetime import get_tzinfo


class ProposalLearningUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.ProposalLearningUnit"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
    learning_unit_year = factory.SubFactory(LearningUnitYearFakerFactory)
    type = factory.Iterator(proposal_type.CHOICES, getter=operator.itemgetter(0))
    state = factory.Iterator(proposal_state.CHOICES, getter=operator.itemgetter(0))
    initial_data = {}
    entity = factory.SubFactory(EntityFactory)
    folder_id = factory.fuzzy.FuzzyInteger(100)