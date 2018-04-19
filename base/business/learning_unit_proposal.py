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

from django.contrib.messages import ERROR, SUCCESS
from django.forms import model_to_dict
from django.utils.translation import ugettext_lazy as _

from base import models as mdl_base
from base.business.learning_units.edition import update_or_create_entity_container_year_with_components, \
    edit_learning_unit_end_date
from base.business.learning_units.perms import PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES
from base.business.learning_units.simple import deletion as business_deletion, deletion
from base.models import entity_container_year, campus, entity
from base.models.enums import proposal_state, proposal_type
from base.models.enums.entity_container_year_link_type import ENTITY_TYPE_LIST
from base.models.enums.proposal_type import ProposalType
from base.utils import send_mail as send_mail_util
from reference.models import language

APP_BASE_LABEL = 'base'
END_FOREIGN_KEY_NAME = "_id"
NO_PREVIOUS_VALUE = '-'
# TODO : VALUES_WHICH_NEED_TRANSLATION ?
VALUES_WHICH_NEED_TRANSLATION = ["periodicity", "container_type", "internship_subtype"]
LABEL_ACTIVE = _('active')
LABEL_INACTIVE = _('inactive')


def compute_proposal_type(proposal_learning_unit_year):
    if proposal_learning_unit_year.type in [ProposalType.CREATION.name, ProposalType.SUPPRESSION.name]:
        return proposal_learning_unit_year.type

    differences = get_difference_of_proposal(proposal_learning_unit_year)
    if differences.get('acronym') and len(differences) == 1:
        return ProposalType.TRANSFORMATION.name
    elif differences.get('acronym'):
        return ProposalType.TRANSFORMATION_AND_MODIFICATION.name
    else:
        return ProposalType.MODIFICATION.name


def reinitialize_data_before_proposal(learning_unit_proposal):
    learning_unit_year = learning_unit_proposal.learning_unit_year
    initial_data = learning_unit_proposal.initial_data
    _reinitialize_model_before_proposal(learning_unit_year, initial_data["learning_unit_year"])
    _reinitialize_model_before_proposal(learning_unit_year.learning_unit, initial_data["learning_unit"])
    _reinitialize_model_before_proposal(learning_unit_year.learning_container_year,
                                        initial_data["learning_container_year"])
    _reinitialize_entities_before_proposal(learning_unit_year.learning_container_year,
                                           initial_data["entities"])


def _reinitialize_model_before_proposal(obj_model, attribute_initial_values):
    for attribute_name, attribute_value in attribute_initial_values.items():
        if attribute_name != "id":
            cleaned_initial_value = _clean_attribute_initial_value(attribute_name, attribute_value)
            setattr(obj_model, attribute_name, cleaned_initial_value)
    obj_model.save()


def _clean_attribute_initial_value(attribute_name, attribute_value):
    clean_attribute_value = attribute_value
    if attribute_name == "campus":
        clean_attribute_value = campus.find_by_id(attribute_value)
    elif attribute_name == "language":
        clean_attribute_value = language.find_by_id(attribute_value)
    return clean_attribute_value


def _reinitialize_entities_before_proposal(learning_container_year, initial_entities_by_type):
    for type_entity, id_entity in initial_entities_by_type.items():
        initial_entity = entity.get_by_internal_id(id_entity)
        if initial_entity:
            update_or_create_entity_container_year_with_components(initial_entity, learning_container_year, type_entity)
        else:
            current_entity_container_year = entity_container_year.find_by_learning_container_year_and_linktype(
                learning_container_year, type_entity)
            if current_entity_container_year is not None:
                current_entity_container_year.delete()


def delete_learning_unit_proposal(learning_unit_proposal):
    prop_type = learning_unit_proposal.type
    lu = learning_unit_proposal.learning_unit_year.learning_unit
    learning_unit_proposal.delete()
    if prop_type == ProposalType.CREATION.name:
        lu.delete()


def get_difference_of_proposal(learning_unit_yr_proposal):
    initial_data = learning_unit_yr_proposal.initial_data
    actual_data = _copy_learning_unit_data(learning_unit_yr_proposal.learning_unit_year)
    differences = {}
    for model in ['learning_unit', 'learning_unit_year', 'learning_container_year', 'entities']:
        initial_data_by_model = initial_data.get(model)
        if not initial_data_by_model:
            continue

        differences.update(
            {key: initial_data_by_model[key] for key, value in initial_data_by_model.items()
             if value != actual_data[model][key]})
    return differences


def _replace_key_of_foreign_key(data):
    return {key_name.replace(END_FOREIGN_KEY_NAME, ''): data[key_name] for key_name in data.keys()}


def _compare_initial_current_data(current_data, initial_data):
    corrected_dict = _replace_key_of_foreign_key(current_data)
    differences = {}
    for attribute, initial_value in initial_data.items():
        if attribute in corrected_dict and initial_data.get(attribute, None) != corrected_dict.get(attribute):
            differences.update(_get_the_old_value(attribute, current_data, initial_data))
    return differences


def _get_the_old_value(key, current_data, initial_data):
    initial_value = initial_data.get(key) or NO_PREVIOUS_VALUE

    if _is_foreign_key(key, current_data):
        return _get_str_representing_old_data_from_foreign_key(key, initial_value)
    else:
        return _get_old_value_when_not_foreign_key(initial_value, key)


def _get_str_representing_old_data_from_foreign_key(key, initial_value):
    if initial_value != NO_PREVIOUS_VALUE:
        return _get_old_value_of_foreign_key(key, initial_value)
    else:
        return {key: NO_PREVIOUS_VALUE}


def _get_old_value_of_foreign_key(key, initial_value):
    differences = {}
    if key == 'campus':
        differences.update({key: str(mdl_base.campus.find_by_id(initial_value))})

    if key == 'language':
        differences.update({key: str(language.find_by_id(initial_value))})
    return differences


def _is_foreign_key(key, current_data):
    return "{}{}".format(key, END_FOREIGN_KEY_NAME) in current_data


def _get_status_initial_value(initial_value, key):
    return {key: LABEL_ACTIVE} if initial_value else {key: LABEL_INACTIVE}


def _get_old_value_when_not_foreign_key(initial_value, key):
    if key in VALUES_WHICH_NEED_TRANSLATION and initial_value != NO_PREVIOUS_VALUE:
        return {key: "{}".format(_(initial_value))}
    elif key == 'status':
        return _get_status_initial_value(initial_value, key)
    else:
        return {key: "{}".format(initial_value)}


def cancel_proposals(proposals, author):
    return apply_action_on_proposals(proposals, author, cancel_proposal, "success_cancel_proposal",
                                     "error_cancel_proposal",
                                     send_mail_util.send_mail_after_the_learning_unit_proposal_cancellation)


def consolidate_proposals(proposals, author):
    return apply_action_on_proposals(proposals, author, consolidate_proposal, "success_consolidate_proposal",
                                     "error_consolidate_proposal",
                                     send_mail_util.send_mail_after_the_learning_unit_proposal_consolidation)


def apply_action_on_proposals(proposals, author, action_method, success_msg_id, error_msg_id, send_mail_method):
    messages_by_level = {SUCCESS: [], ERROR: []}

    for proposal in proposals:
        msg = action_method(proposal)
        if msg.get(ERROR):
            error_msg = _(error_msg_id).format(acronym=proposal.learning_unit_year.acronym,
                                               academic_year=proposal.learning_unit_year.academic_year)
            messages_by_level[ERROR].append(error_msg)
        else:
            success_msg = _(success_msg_id).format(acronym=proposal.learning_unit_year.acronym,
                                                   academic_year=proposal.learning_unit_year.academic_year)
            messages_by_level[SUCCESS].append(success_msg)

    send_mail_method([author], proposals)
    return messages_by_level


def cancel_proposal(learning_unit_proposal, author=None, send_mail=False):
    acronym = learning_unit_proposal.learning_unit_year.acronym
    academic_year = learning_unit_proposal.learning_unit_year.academic_year
    error_messages = []
    success_messages = []
    if learning_unit_proposal.type == ProposalType.CREATION.name:
        learning_unit_year = learning_unit_proposal.learning_unit_year
        error_messages.extend(business_deletion.check_can_delete_ignoring_proposal_validation(learning_unit_year))
        if not error_messages:
            success_messages.extend(business_deletion.delete_from_given_learning_unit_year(learning_unit_year))
    else:
        reinitialize_data_before_proposal(learning_unit_proposal)
    delete_learning_unit_proposal(learning_unit_proposal)
    success_messages.append(_("success_cancel_proposal").format(acronym=acronym,
                                                                academic_year=academic_year))
    if send_mail and author is not None:
        send_mail_util.send_mail_after_the_learning_unit_proposal_cancellation([author], [learning_unit_proposal])
    return {
        SUCCESS: success_messages,
        ERROR: error_messages
    }


def consolidate_proposal(proposal, author=None, send_mail=False):
    messages_by_level = {}
    if proposal.state not in PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES:
        return {
            ERROR: [_("error_consolidate_proposal").format(acronym=proposal.learning_unit_year.acronym,
                                                           academic_year=proposal.learning_unit_year.academic_year)]
        }
    if proposal.type == proposal_type.ProposalType.CREATION.name:
        messages_by_level = consolidate_creation_proposal(proposal)

    if send_mail and author is not None:
        send_mail_util.send_mail_after_the_learning_unit_proposal_consolidation([author], [proposal])

    return messages_by_level


def consolidate_creation_proposal(proposal):
    proposal.learning_unit_year.learning_unit.end_year = proposal.learning_unit_year.academic_year.year
    proposal.learning_unit_year.learning_unit.save()

    if proposal.state == proposal_state.ProposalState.ACCEPTED.name:
        results = _consolidate_creation_proposal_of_state_accepted(proposal)
    else:
        results = _consolidate_creation_proposal_of_state_refused(proposal)
    if not results.get(ERROR, []):
        proposal.delete()
    return results


def _consolidate_creation_proposal_of_state_accepted(proposal):
    return {SUCCESS: edit_learning_unit_end_date(proposal.learning_unit_year.learning_unit, None)}


def _consolidate_creation_proposal_of_state_refused(proposal):
    messages_by_level = deletion.check_learning_unit_deletion(proposal.learning_unit_year.learning_unit,
                                                              check_proposal=False)
    if messages_by_level:
        return {ERROR: list(messages_by_level.values())}
    return {SUCCESS: deletion.delete_learning_unit(proposal.learning_unit_year.learning_unit)}


def compute_proposal_state(a_person):
    return proposal_state.ProposalState.CENTRAL.name if a_person.is_central_manager() \
        else proposal_state.ProposalState.FACULTY.name


def _copy_learning_unit_data(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year
    entities_by_type = entity_container_year.find_entities_grouped_by_linktype(learning_container_year)

    learning_container_year_values = _get_attributes_values(learning_container_year,
                                                            ["id", "acronym", "common_title", "common_title_english",
                                                             "container_type", "campus", "language", "in_charge"])
    learning_unit_values = _get_attributes_values(learning_unit_year.learning_unit, ["id", "periodicity", "end_year"])
    learning_unit_year_values = _get_attributes_values(learning_unit_year, ["id", "acronym", "specific_title",
                                                                            "specific_title_english",
                                                                            "internship_subtype", "quadrimester",
                                                                            "status"])
    learning_unit_year_values["credits"] = float(learning_unit_year.credits) if learning_unit_year.credits else None
    return get_initial_data(entities_by_type, learning_container_year_values, learning_unit_values,
                            learning_unit_year_values)


def _get_attributes_values(obj, attributes_name):
    return model_to_dict(obj, fields=attributes_name)


def get_initial_data(entities_by_type, learning_container_year_values, learning_unit_values, learning_unit_year_values):
    initial_data = {
        "learning_container_year": learning_container_year_values,
        "learning_unit_year": learning_unit_year_values,
        "learning_unit": learning_unit_values,
        "entities": get_entities(entities_by_type)
    }
    return initial_data


def get_entities(entities_by_type):
    return {entity_type: get_entity_by_type(entity_type, entities_by_type) for entity_type in ENTITY_TYPE_LIST}


def get_entity_by_type(entity_type, entities_by_type):
    if entities_by_type.get(entity_type):
        return entities_by_type[entity_type].id
    else:
        return None
