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
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business import learning_unit_year_with_context
from base.business.learning_unit import CMS_LABEL_PEDAGOGY, get_cms_label_data
from base.business.learning_units.edition import ConsistencyError
from base.forms.learning_unit.edition import LearningUnitEndDateForm
from base.forms.learning_unit.edition_volume import VolumeEditionFormsetContainer
from base.forms.learning_unit.learning_unit_create_2 import FullForm, PartimForm
from base.forms.learning_unit_pedagogy import SummaryModelForm, LearningUnitPedagogyForm, \
    BibliographyModelForm
from base.models.bibliography import Bibliography
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views import layout
from base.views.common import display_error_messages, display_success_messages
from base.views.learning_unit import get_learning_unit_identification_context, \
    get_common_context_learning_unit_year, learning_unit_components
from base.views.learning_units import perms


@login_required
@permission_required('base.can_edit_learningunit_date', raise_exception=True)
@perms.can_perform_end_date_modification
def learning_unit_edition_end_date(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    person = get_object_or_404(Person, user=request.user)

    context = get_learning_unit_identification_context(learning_unit_year_id, person)

    learning_unit_to_edit = learning_unit_year.learning_unit
    form = LearningUnitEndDateForm(request.POST or None, learning_unit=learning_unit_to_edit)
    if form.is_valid():
        try:
            result = form.save()
            display_success_messages(request, result, extra_tags='safe')

            learning_unit_year_id = _get_current_learning_unit_year_id(learning_unit_to_edit, learning_unit_year_id)

            return HttpResponseRedirect(reverse('learning_unit', args=[learning_unit_year_id]))

        except IntegrityError as e:
            display_error_messages(request, e.args[0])

    context['form'] = form
    return layout.render(request, 'learning_unit/simple/update_end_date.html', context)


def _get_current_learning_unit_year_id(learning_unit_to_edit, learning_unit_year_id):
    if not LearningUnitYear.objects.filter(pk=learning_unit_year_id).exists():
        result = LearningUnitYear.objects.filter(learning_unit=learning_unit_to_edit).last().pk
    else:
        result = learning_unit_year_id
    return result


@login_required
@permission_required('base.can_edit_learningunit', raise_exception=True)
@perms.can_perform_learning_unit_modification
def update_learning_unit(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    person = get_object_or_404(Person, user=request.user)

    if learning_unit_year.subtype == learning_unit_year_subtypes.FULL:
        learning_unit_form_container = FullForm(request.POST or None, person, instance=learning_unit_year)
    else:
        learning_unit_form_container = PartimForm(request.POST or None, person,
                                                  learning_unit_year_full=learning_unit_year.parent,
                                                  instance=learning_unit_year)

    if learning_unit_form_container.is_valid():
        _save_form_and_display_messages(request, learning_unit_form_container)
        return redirect('learning_unit', learning_unit_year_id=learning_unit_year_id)

    context = learning_unit_form_container.get_context()
    context["learning_unit_year"] = learning_unit_year

    return render(request, 'learning_unit/simple/update.html', context)


@login_required
@permission_required('base.can_edit_learningunit', raise_exception=True)
@perms.can_perform_learning_unit_modification
def learning_unit_volumes_management(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)

    context['learning_units'] = learning_unit_year_with_context.get_with_context(
        learning_container_year_id=context['learning_unit_year'].learning_container_year_id
    )

    volume_edition_formset_container = VolumeEditionFormsetContainer(request, context['learning_units'], person)

    if volume_edition_formset_container.is_valid() and not request.is_ajax():
        _save_form_and_display_messages(request, volume_edition_formset_container)
        return HttpResponseRedirect(reverse(learning_unit_components, args=[learning_unit_year_id]))

    context['formsets'] = volume_edition_formset_container.formsets
    context['tab_active'] = 'components'
    context['experimental_phase'] = True
    if request.is_ajax():
        return JsonResponse({'errors': volume_edition_formset_container.errors})

    return layout.render(request, "learning_unit/volumes_management.html", context)


def _save_form_and_display_messages(request, form):
    records = None
    try:
        records = form.save()
        display_success_messages(request, _('success_modification_learning_unit'))
    except ConsistencyError as e:
        error_list = e.error_list
        error_list.insert(0, _('The learning unit has been updated until %(year)s.')
                          % {'year': e.last_instance_updated.academic_year})
        display_error_messages(request, e.error_list)
    return records


def update_learning_unit_pedagogy(request, learning_unit_year_id, context, template):
    person = get_object_or_404(Person, user=request.user)
    context.update(get_common_context_learning_unit_year(learning_unit_year_id, person))
    learning_unit_year = context['learning_unit_year']
    perm_to_edit = int(request.user.has_perm('can_edit_learningunit_pedagogy'))

    post = request.POST or None
    summary_form = SummaryModelForm(post, person, context['is_person_linked_to_entity'], instance=learning_unit_year)
    BibliographyFormset = inlineformset_factory(LearningUnitYear, Bibliography, fields=('title', 'mandatory'),
                                                max_num=10, extra=perm_to_edit, form=BibliographyModelForm,
                                                can_delete=perm_to_edit)
    bibliography_formset = BibliographyFormset(post, instance=learning_unit_year, form_kwargs={'person': person})

    if perm_to_edit and summary_form.is_valid() and bibliography_formset.is_valid():
        try:
            summary_form.save()
            bibliography_formset.save()

            display_success_messages(request, _("success_modification_learning_unit"))
            # Redirection on the same page
            return HttpResponseRedirect(request.path_info)

        except ValueError as e:
            display_error_messages(request, e.args[0])

    context.update(get_cms_pedagogy_form(request, learning_unit_year))
    context['summary_editable_form'] = summary_form
    context['bibliography_formset'] = bibliography_formset
    return layout.render(request, template, context)


# TODO Method similar with all cms forms
def get_cms_pedagogy_form(request, learning_unit_year):
    user_language = mdl.person.get_user_interface_language(request.user)
    return {
        'cms_labels_translated': get_cms_label_data(CMS_LABEL_PEDAGOGY, user_language),
        'form_french': LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                language_code=settings.LANGUAGE_CODE_FR),
        'form_english': LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                 language_code=settings.LANGUAGE_CODE_EN)
        }


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    context = {'experimental_phase': True}
    template = "learning_unit/pedagogy.html"
    return update_learning_unit_pedagogy(request, learning_unit_year_id, context, template)
