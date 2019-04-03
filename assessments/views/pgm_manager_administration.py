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
import json

from dal import autocomplete
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, FormView

from base import models as mdl
from base.models.entity_manager import is_entity_manager, has_perm_entity_manager
from base.models.offer_year import OfferYear
from base.models.person import Person
from base.models.program_manager import ProgramManager
from base.views.mixins import AjaxTemplateMixin

ALL_OPTION_VALUE = "-"
ALL_OPTION_VALUE_ENTITY = "all_"


@login_required
@user_passes_test(has_perm_entity_manager)
def pgm_manager_administration(request):
    administrator_entities = get_administrator_entities(request.user)
    current_academic_yr = mdl.academic_year.current_academic_year()
    return render(request, "admin/pgm_manager.html", {
        'academic_year': current_academic_yr,
        'administrator_entities_string': _get_administrator_entities_acronym_list(administrator_entities),
        'entities_managed_root': administrator_entities,
        'offer_types': mdl.offer_type.find_all(),
        'managers': _get_entity_program_managers(administrator_entities, current_academic_yr),
        'init': '1'})


class ProgramManagerList(ListView):
    model = Person
    template_name = "admin/programmanager_list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        offer_years = self.request.GET.getlist('offer_year')
        if not offer_years:
            return qs.none()

        for offer_year in offer_years:
            qs = qs.filter(programmanager__offer_year=offer_year)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer_years'] = self.request.GET.getlist('offer_year')
        return context


class ProgramManagerDeleteView(UserPassesTestMixin, AjaxTemplateMixin, DeleteView):
    model = ProgramManager
    success_url = reverse_lazy('manager_list')
    template_name = 'admin/programmanager_confirm_delete_inner.html'
    partial_reload = '#pnl_managers'

    def test_func(self):
        return is_entity_manager(self.request.user)

    @property
    def offer_years(self) -> list:
        return self.request.GET['offer_year'].split(',')

    def get_success_url(self):
        url = super().get_success_url() + "?"
        for oy in self.offer_years:
            url += "offer_year={}&".format(oy)
        return url

    def get_object(self, queryset=None):
        return self.model.objects.filter(
            person__pk=self.kwargs['pk'],
            offer_year__in=self.offer_years
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        for obj in self.object.all():
            obj.delete()
        return self._ajax_response() or HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Person.objects.get(pk=self.kwargs['pk'])
        context['manager'] = manager
        context['offer_years'] = OfferYear.objects.filter(pk__in=self.offer_years)
        context['other_offer_years'] = OfferYear.objects.filter(programmanager__person=manager) \
            .exclude(pk__in=self.offer_years)
        return context


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, item):
        return "{} {}, {}".format(item.last_name, item.first_name, item.email)

    def get_queryset(self):
        qs = Person.objects.all()
        if self.q:
            qs = qs.filter(Q(last_name__icontains=self.q) | Q(first_name__icontains=self.q))
        return qs.order_by('last_name', 'first_name')


class ProgramManagerForm(ModelForm):
    class Meta:
        model = ProgramManager
        fields = ('person',)
        widgets = {'person': autocomplete.ModelSelect2(url='person-autocomplete', attrs={'style': 'width:100%'})}


class ProgramManagerCreateView(UserPassesTestMixin, AjaxTemplateMixin, FormView):
    form_class = ProgramManagerForm
    success_url = reverse_lazy('manager_list')
    template_name = 'admin/manager_add_inner.html'
    partial_reload = '#pnl_managers'

    def test_func(self):
        return is_entity_manager(self.request.user)

    @property
    def offer_years(self) -> list:
        return self.request.GET['offer_year'].split(',')

    def get_success_url(self):
        url = super().get_success_url() + "?"
        for oy in self.offer_years:
            url += "offer_year={}&".format(oy)
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offer_years'] = self.request.GET['offer_year']
        return context

    def form_valid(self, form):
        offer_years = OfferYear.objects.filter(
            pk__in=self.request.GET['offer_year'].split(',')
        )
        person = form.cleaned_data['person']
        for oy in offer_years:
            ProgramManager.objects.get_or_create(
                person=person,
                offer_year=oy
            )
        return super().form_valid(form)


@login_required
def pgm_manager_search(request):
    person_id = get_filter_value(request, 'person')
    manager_person = None
    if person_id:
        manager_person = mdl.person.find_by_id(person_id)

    entity_selected = get_filter_value(request, 'entity')  # if an acronym is selected this value is not none
    entity_root_selected = None  # if an 'all hierarchy of' is selected this value is not none

    if entity_selected is None:
        entity_root_selected = get_entity_root_selected(request)

    pgm_offer_type = get_filter_value(request, 'offer_type')

    administrator_entities = get_administrator_entities(request.user)

    current_academic_yr = mdl.academic_year.current_academic_year()

    data = {
        'academic_year': current_academic_yr,
        'person': manager_person,
        'administrator_entities_string': _get_administrator_entities_acronym_list(administrator_entities),
        'entities_managed_root': administrator_entities,
        'entity_selected': entity_selected,
        'entity_root_selected': entity_root_selected,
        'offer_types': mdl.offer_type.find_all(),
        'pgms': _get_programs(current_academic_yr,
                              get_entity_list(entity_selected, get_entity_root(entity_root_selected)),
                              manager_person,
                              pgm_offer_type),
        'managers': _get_entity_program_managers(administrator_entities, current_academic_yr),
        'offer_type': pgm_offer_type
    }
    return render(request, "admin/pgm_manager.html", data)


def get_entity_root(entity_selected):
    if entity_selected:
        return mdl.structure.find_by_id(entity_selected)
    return None


def get_entity_root_selected(request):
    entity_root_selected = get_filter_value_entity(request, 'entity')
    if entity_root_selected is None:
        entity_root_selected = request.POST.get('entity_root', None)
    return entity_root_selected


def get_managed_entities(entity_managed_list):
    if entity_managed_list:
        structures = []
        for entity_managed in entity_managed_list:
            children_acronyms = find_values('acronym', json.dumps(entity_managed['root'].serializable_object()))
            structures.extend(mdl.structure.find_by_acronyms(children_acronyms))
        return sorted(structures, key=lambda a_structure: a_structure.acronym)

    return None


def get_entity_list(entity, entity_managed_structure):
    if entity:
        entity_found = mdl.structure.find_by_id(entity)
        if entity_found:
            return [entity_found]
    else:
        children_acronyms = find_values('acronym', json.dumps(entity_managed_structure.serializable_object()))
        return mdl.structure.find_by_acronyms(children_acronyms)

    return None


@login_required
def get_filter_value(request, value_name):
    value = _get_request_value(request, value_name)

    if value == ALL_OPTION_VALUE or value == '' or value.startswith(ALL_OPTION_VALUE_ENTITY):
        return None
    return value


def get_administrator_entities(a_user):
    structures = []
    for entity_managed in mdl.entity_manager.find_by_user(a_user):
        children_acronyms = find_values('acronym', json.dumps(entity_managed.structure.serializable_object()))
        structures.append({'root': entity_managed.structure,
                           'structures': mdl.structure.find_by_acronyms(children_acronyms)})
    return structures


def _get_programs(academic_yr, entity_list, manager_person, an_offer_type):
    qs = OfferYear.objects.filter(
        academic_year=academic_yr,
        entity_management__in=entity_list,
    )

    if an_offer_type:
        qs = qs.filter(offer_type=an_offer_type)

    if manager_person:
        qs = qs.filter(programmanager__person=manager_person)
    return qs.distinct()


def _get_entity_program_managers(entity, academic_yr):
    entities = get_managed_entities(entity)
    return mdl.program_manager.find_by_management_entity(entities, academic_yr)


def find_values(key_value, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[key_value])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict)  # return value ignored
    return results


@login_required
def get_filter_value_entity(request, value_name):
    value = _get_request_value(request, value_name)
    if value != '' and value.startswith(ALL_OPTION_VALUE_ENTITY):
        return value.replace(ALL_OPTION_VALUE_ENTITY, "")

    return None


def _get_request_value(request, value_name):
    if request.method == 'POST':
        value = request.POST.get(value_name, None)
    else:
        value = request.GET.get(value_name, None)
    return value


def _get_administrator_entities_acronym_list(administrator_entities):
    """
    Return a list of acronyms separated by comma.  List of the acronyms administrate by the user
    :param administrator_entities:
    :return:
    """
    return ', '.join(str(entity_manager['root'].acronym) for entity_manager in administrator_entities)
