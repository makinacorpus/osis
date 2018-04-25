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
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, get_object_or_404

from base.business import learning_unit_proposal as business_proposal
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.common import display_messages_by_level
from base.views.learning_units import perms


@login_required
@perms.can_perform_cancel_proposal
@permission_required('base.can_propose_learningunit', raise_exception=True)
def cancel_proposal_of_learning_unit(request, learning_unit_year_id):
    user_person = get_object_or_404(Person, user=request.user)
    learning_unit_proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year=learning_unit_year_id)
    messages_by_level = business_proposal.cancel_proposals_and_send_report([learning_unit_proposal], user_person, {})
    display_messages_by_level(request, messages_by_level)

    if LearningUnitYear.objects.filter(pk=learning_unit_year_id).exists():
        return redirect('learning_unit', learning_unit_year_id=learning_unit_year_id)

    return redirect('learning_units_proposal')
