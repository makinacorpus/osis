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
import itertools
import json
from collections import namedtuple, defaultdict

from ckeditor.widgets import CKEditorWidget
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, TemplateView
from reversion.models import Version

from base import models as mdl
from base.business import education_group as education_group_business
from base.business.education_groups import general_information
from base.business.education_groups.general_information import PublishException
from base.business.education_groups.general_information_sections import SECTION_LIST, \
    MIN_YEAR_TO_DISPLAY_GENERAL_INFO_AND_ADMISSION_CONDITION, SECTIONS_PER_OFFER_TYPE, CONTACTS
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import starting_academic_year
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_year import EducationGroupYear
from base.models.education_group_year_domain import EducationGroupYearDomain
from base.models.enums import education_group_categories, academic_calendar_type
from base.models.enums.education_group_categories import TRAINING
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.mandatary import Mandatary
from base.models.offer_year_calendar import OfferYearCalendar
from base.models.program_manager import ProgramManager
from base.utils.cache import cache, ElementCache
from base.utils.cache_keys import get_tab_lang_keys
from base.views.common import display_error_messages, display_success_messages
from base.views.education_groups.select import get_clipboard_content_display
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from education_group.models.group_year import GroupYear
from program_management.ddd.repositories import load_tree, load_node
from program_management.ddd.repositories.find_roots import find_roots
from program_management.ddd.service import tree_service
from program_management.forms.custom_xls import CustomXlsForm
from program_management.models.enums import node_type
from webservices.business import CONTACT_INTRO_KEY
from program_management.ddd.repositories.load_tree import find_all_program_tree_versions, \
    find_all_versions_academic_year
from django.db.models import Prefetch
from program_management.serializers.program_tree_view import program_tree_view_serializer


SECTIONS_WITH_TEXT = (
    'ucl_bachelors',
    'others_bachelors_french',
    'bachelors_dutch',
    'foreign_bachelors',
    'graduates',
    'masters'
)

NUMBER_SESSIONS = 3

LEARNING_UNIT_YEAR = LearningUnitYear._meta.db_table
EDUCATION_GROUP_YEAR = EducationGroupYear._meta.db_table


class CatalogGenericDetailView:
    def get_selected_element_for_clipboard(self):
        cached_data = ElementCache(self.request.user).cached_data
        if cached_data:
            obj = self._get_instance_object_from_cache(cached_data)
            return get_clipboard_content_display(obj, cached_data['action'])
        return None

    @staticmethod
    def _get_instance_object_from_cache(cached_data):
        model_name = cached_data.get('modelname')
        cached_obj_id = cached_data.get('id')
        obj = None
        if model_name == LEARNING_UNIT_YEAR:
            obj = LearningUnitYear.objects.get(id=cached_obj_id)
        elif model_name == EDUCATION_GROUP_YEAR:
            obj = EducationGroupYear.objects.get(id=cached_obj_id)
        return obj


@method_decorator(login_required, name='dispatch')
class EducationGroupGenericDetailView(PermissionRequiredMixin, CatalogGenericDetailView, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True

    # FIXME: resolve dependency in other ways
    with_tree = 'program_management' in settings.INSTALLED_APPS

    def get_object(self):
        # TODO: Use DDD instead DDD
        return get_object_or_404(
            GroupYear.objects.select_related(
                'educationgroupversion__offer',
                'management_entity',
                'academic_year',
            ),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )

    @cached_property
    def object(self):
        return self.get_object()

    def get_tree(self):
        if self.with_tree:
            # TODO : Create Path class
            element_id = self.get_node_path().split("|")[0]
            return load_tree.load(int(element_id))
        return None

    def get_node_path(self):
        return self.request.GET.get('path') or str(self.get_object().element.pk)

    @cached_property
    def node(self):
        """
        Return the current node based on path encoded in path? querystring
        """
        path = self.get_node_path()
        return self.get_tree().get_node(path)

    @cached_property
    def person(self):
        return self.request.user.person

    def has_version_related(self):
        return hasattr(self.object, 'educationgroupversion') and self.object.educationgroupversion

    @cached_property
    def offer(self):
        return self.get_object().educationgroupversion.offer

    @cached_property
    def version_name(self):
        return self.get_object().educationgroupversion.version_name

    @cached_property
    def transition(self):
        return self.get_object().educationgroupversion.is_transition

    @cached_property
    def all_versions_available(self):
        return find_all_program_tree_versions(self.offer.acronym, self.offer.academic_year.year, False)

    @cached_property
    def current_version(self):
        return next((version for version in self.all_versions_available if
                     version.version_name == self.version_name and version.is_transition == self.transition), None)

    @cached_property
    def starting_academic_year(self):
        return starting_academic_year()

    def get_context_data(self, **kwargs):
        can_change_education_group = self.request.user.has_perm(
            'base.change_educationgroup',
            self.object
        )
        context = {
            **super().get_context_data(**kwargs),
            "person": self.person,
            "node": self.node,
            "group_year": self.object,
            "group_to_parent": self.request.GET.get("group_to_parent") or '0',
            "enums": mdl.enums.education_group_categories,
            "current_academic_year": self.starting_academic_year,
            "selected_element_clipboard": self.get_selected_element_for_clipboard(),
            "form_xls_custom": CustomXlsForm(),
            "can_change_education_group": can_change_education_group,
        }

        if self.has_version_related():
            context.update(self.get_offer_context_data())
        else:
            context.update(self.get_group_context_data())

        program_tree = self.get_tree()
        if program_tree:
            serialized_data = program_tree_view_serializer(program_tree)
            context['tree'] = json.dumps(serialized_data)
            context["current_node"] = program_tree.get_node_by_id_and_type(
                self.object.id,
                node_type.NodeType.EDUCATION_GROUP
            )
            context["node_path"] = program_tree.get_node_smallest_ordered_path(context["current_node"])
        return context

    def get_offer_context_data(self):
        can_change_coorganization = self.request.user.has_perm('base.change_educationgrouporganization', self.offer)
        return {
            "current_version": self.current_version,
            "offer": self.offer,
            "offer_id": self.offer.pk,
            "parent_training": self.offer.parent_by_training(),
            "all_versions_available": self.all_versions_available,
            "academic_years":  find_all_versions_academic_year(self.offer.acronym, self.version_name, self.transition),
            "can_change_coorganization": can_change_coorganization
        }

    def get_group_context_data(self):
        return {
            "show_identification": True,
            "show_utilization": True,
            "show_content": True,
            "show_general_information": False,
            "show_skills_and_achievements": False,
            "show_administrative": False,
            "show_diploma": False,
            "show_admission_conditions": False,
        }

    def get(self, request, *args, **kwargs):
        default_url = reverse('education_group_read', kwargs={
            'year': self.object.academic_year.year,
            'code': self.object.partial_acronym
        })
        if self.request.GET.get('group_to_parent'):
            default_url += '?group_to_parent=' + self.request.GET.get('group_to_parent')
        if not self.can_show_view():
            return HttpResponseRedirect(default_url)
        return super().get(request, *args, **kwargs)

    def can_show_view(self):
        return True

    def show_identification(self):
        return True

    def show_diploma(self):
        return self.object.education_group_type.category == TRAINING and not self.offer.is_common \
               and self.current_version.is_standard

    def show_general_information(self):
        return not self.object.acronym.startswith('common-') and \
               self.is_general_info_and_condition_admission_in_display_range() and \
               self.object.education_group_type.name in SECTIONS_PER_OFFER_TYPE.keys() and \
               self.current_version.is_standard

    def show_administrative(self):
        return self.object.education_group_type.category == TRAINING and \
               self.object.education_group_type.name not in [TrainingType.PGRM_MASTER_120.name,
                                                             TrainingType.PGRM_MASTER_180_240.name] and \
               not self.offer.is_common \
               and self.current_version.is_standard

    def show_content(self):
        return not(self.has_version_related() and self.offer.is_common)

    def show_utilization(self):
        return not(self.has_version_related() and self.offer.is_common)

    def show_admission_conditions(self):
        return self.has_version_related() and not self.offer.is_main_common and \
               self.offer.education_group_type.name in itertools.chain(TrainingType.with_admission_condition(),
                                                                       MiniTrainingType.with_admission_condition()) \
               and self.is_general_info_and_condition_admission_in_display_range()\
               and self.current_version.is_standard

    def show_skills_and_achievements(self):
        return self.has_version_related() and not self.offer.is_common and \
               self.offer.education_group_type.name in itertools.chain(TrainingType.with_skills_achievements(),
                                                                       MiniTrainingType.with_admission_condition()) \
               and self.is_general_info_and_condition_admission_in_display_range() \
               and self.current_version.is_standard

    def is_general_info_and_condition_admission_in_display_range(self):
        return MIN_YEAR_TO_DISPLAY_GENERAL_INFO_AND_ADMISSION_CONDITION <= self.object.academic_year.year < \
               self.starting_academic_year.year + 2


class EducationGroupRead(EducationGroupGenericDetailView):
    templates = {
        education_group_categories.TRAINING: "education_group/identification_training_details.html",
        education_group_categories.MINI_TRAINING: "education_group/identification_mini_training_details.html",
        education_group_categories.GROUP: "education_group/identification_group_details.html"
    }

    def can_show_view(self):
        return self.show_identification()

    def get_offer_context_data(self):
        education_group_languages = self.offer.educationgrouplanguage_set.order_by('order').values_list(
            'language__name', flat=True)
        return {
            **super().get_offer_context_data(),
            "education_group_languages": education_group_languages,
            "versions": self.get_related_versions(),
            "show_coorganization": education_group_business.has_coorganization(self.offer),
            "is_finality_types": self.offer.is_finality,
            "education_group_year": self.offer
        }

    def get_template_names(self):
        return self.templates.get(self.object.education_group_type.category)

    def get_related_versions(self):
        versions = Version.objects.get_for_object(self.object).select_related('revision__user__person')

        related_models = [
            EducationGroupOrganization,
            EducationGroupAchievement,
            EducationGroupDetailedAchievement,
            EducationGroupYearDomain,
            EducationGroupCertificateAim
        ]

        subversion = Version.objects.none()
        for model in related_models:
            subversion |= Version.objects.get_for_model(model).select_related('revision__user__person')

        versions |= subversion.filter(
            serialized_data__contains="\"education_group_year\": {}".format(self.object.pk)
        )

        return versions.order_by('-revision__date_created').distinct('revision__date_created')


class EducationGroupDiplomas(EducationGroupGenericDetailView):
    template_name = "education_group/tab_diplomas.html"

    def can_show_view(self):
        return self.show_diploma()


class EducationGroupGeneralInformation(EducationGroupGenericDetailView):
    template_name = "education_group/tab_general_informations.html"

    def can_show_view(self):
        return self.show_general_information()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_common_education_group_year = self.object.acronym.startswith('common')
        common_education_group_year = None
        if not is_common_education_group_year:
            common_education_group_year = EducationGroupYear.objects.get_common(
                academic_year=self.object.academic_year,
            )
        sections_to_display = SECTIONS_PER_OFFER_TYPE.get(
            'common' if is_common_education_group_year
            else self.object.education_group_type.name,
            {'specific': [], 'common': []}
        )
        texts = self.get_translated_texts(sections_to_display, common_education_group_year, self.user_language_code)
        show_contacts = CONTACTS in sections_to_display['specific']
        perm_name = 'base.change_commonpedagogyinformation' if self.object.is_common else \
            'base.change_pedagogyinformation'
        context.update({
            'is_common_education_group_year': is_common_education_group_year,
            'sections_with_translated_labels': self.get_sections_with_translated_labels(
                sections_to_display,
                texts
            ),
            'contacts': self._get_publication_contacts_group_by_type(),
            'show_contacts': show_contacts,
            'can_edit_information': self.request.user.has_perm(perm_name, self.object)
        })
        return context

    @cached_property
    def user_language_code(self):
        return mdl.person.get_user_interface_language(self.request.user)

    def get_sections_with_translated_labels(self, sections_to_display, texts):
        # Load the labels
        Section = namedtuple('Section', 'title labels')
        sections_with_translated_labels = []
        for section in SECTION_LIST:
            translated_labels = []
            for label in section.labels:
                translated_labels += self.get_texts_for_label(label, sections_to_display, texts)
            if translated_labels:
                sections_with_translated_labels.append(Section(section.title, translated_labels))
        return sections_with_translated_labels

    def get_texts_for_label(self, label, sections_to_display, texts):
        translated_labels = []
        translated_label = next((text for text in texts['labels'] if text.text_label.label == label), None)
        if label in sections_to_display['common']:
            common_text = self.get_text_structure_for_display(label, texts['common'], translated_label)
            common_text.update({'type': 'common'})
            translated_labels.append(common_text)
        if label in sections_to_display['specific']:
            text = self.get_text_structure_for_display(label, texts['specific'], translated_label)
            text.update({'type': 'specific'})
            translated_labels.append(text)
        return translated_labels

    def get_text_structure_for_display(self, label, texts, translated_label):
        french, english = 'fr-be', 'en'
        text_fr = next(
            (
                text.text for text in texts
                if text.text_label.label == label and text.language == french
            ),
            None
        )
        text_en = next(
            (
                text.text for text in texts
                if text.text_label.label == label and text.language == english
            ),
            None
        )

        return {
            'label': label,
            'translation': translated_label if translated_label else
            (_('This label %s does not exist') % label),
            french: text_fr,
            english: text_en,
        }

    def get_translated_texts(self, sections_to_display, common_edy, user_language):
        if CONTACTS in sections_to_display['specific']:
            sections_to_display['specific'] += [CONTACT_INTRO_KEY]
        specific_texts = TranslatedText.objects.filter(
            text_label__label__in=sections_to_display['specific'],
            entity=entity_name.OFFER_YEAR,
            reference=str(self.object.pk)
        ).select_related("text_label")

        common_texts = TranslatedText.objects.filter(
            text_label__label__in=sections_to_display['common'],
            entity=entity_name.OFFER_YEAR,
            reference=str(common_edy.pk)
        ).select_related("text_label") if common_edy else None

        labels = TranslatedTextLabel.objects.filter(
            text_label__label__in=sections_to_display['common'] + sections_to_display['specific'],
            text_label__entity=entity_name.OFFER_YEAR,
            language=user_language
        ).select_related("text_label")

        return {'common': common_texts, 'specific': specific_texts, 'labels': labels}

    def _get_publication_contacts_group_by_type(self):
        contacts_by_type = {}
        for publication_contact in self.object.educationgrouppublicationcontact_set.all():
            contacts_by_type.setdefault(publication_contact.type, []).append(publication_contact)
        return contacts_by_type


@login_required
@require_http_methods(['POST'])
def publish(request, education_group_year_id, root_id):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)

    try:
        general_information.publish(education_group_year)
        message = _("The program %(acronym)s will be published soon") % {'acronym': education_group_year.acronym}
        display_success_messages(request, message, extra_tags='safe')
    except PublishException as e:
        display_error_messages(request, str(e))

    default_redirect_view = reverse('education_group_general_informations',
                                    kwargs={'root_id': root_id, 'education_group_year_id': education_group_year_id})
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', default_redirect_view))


class EducationGroupAdministrativeData(EducationGroupGenericDetailView):
    template_name = "education_group/tab_administrative_data.html"

    def can_show_view(self):
        return self.show_administrative()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pgm_mgrs = ProgramManager.objects.filter(
            education_group=self.object.education_group,
        ).order_by("person__last_name", "person__first_name")

        mandataries = Mandatary.objects.filter(
            mandate__education_group=self.object.education_group,
            start_date__lte=self.object.academic_year.end_date,
            end_date__gte=self.object.academic_year.start_date
        ).order_by(
            'mandate__function',
            'person__last_name',
            'person__first_name'
        ).select_related("person", "mandate")

        course_enrollment_dates = OfferYearCalendar.objects.filter(
            education_group_year=self.object,
            academic_calendar__reference=academic_calendar_type.COURSE_ENROLLMENT,
            academic_calendar__academic_year=self.object.academic_year
        ).first()

        context.update({
            'course_enrollment_dates': course_enrollment_dates,
            'mandataries': mandataries,
            'pgm_mgrs': pgm_mgrs,
            "can_edit_administrative_data":
                education_group_business.can_user_edit_administrative_data(self.request.user, self.object)
        })
        context.update(get_sessions_dates(self.object))

        return context


def get_sessions_dates(education_group_year):
    calendar_types = (academic_calendar_type.EXAM_ENROLLMENTS, academic_calendar_type.SCORES_EXAM_SUBMISSION,
                      academic_calendar_type.DISSERTATION_SUBMISSION, academic_calendar_type.DELIBERATION,
                      academic_calendar_type.SCORES_EXAM_DIFFUSION)
    calendars = AcademicCalendar.objects.filter(
        reference__in=calendar_types,
        academic_year=education_group_year.academic_year
    ).select_related(
        "sessionexamcalendar"
    ).prefetch_related(
        Prefetch(
            "offeryearcalendar_set",
            queryset=OfferYearCalendar.objects.filter(
                education_group_year=education_group_year
            ),
            to_attr="offer_calendars"
        )
    )

    sessions_dates_by_calendar_type = defaultdict(dict)

    for calendar in calendars:
        session = calendar.sessionexamcalendar
        offer_year_calendars = calendar.offer_calendars
        if offer_year_calendars:
            sessions_dates_by_calendar_type[calendar.reference.lower()]['session{}'.format(session.number_session)] = \
                offer_year_calendars[0]

    return sessions_dates_by_calendar_type


class EducationGroupContent(EducationGroupGenericDetailView):
    template_name = "education_group/tab_content.html"

    def can_show_view(self):
        return self.show_content()

    def get_queryset(self):
        prefetch = Prefetch(
            'groupelementyear_set',
            queryset=GroupElementYear.objects.select_related(
                'child_leaf__learning_container_year',
                'child_branch'
            )
        )
        return super().get_queryset().prefetch_related(prefetch)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_minor_major_option_table'] = self.object.is_minor_major_option_list_choice
        return context


class EducationGroupUsing(EducationGroupGenericDetailView):
    template_name = "education_group/tab_utilization.html"

    def can_show_view(self):
        return self.show_utilization()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trees = tree_service.search_trees_using_node(self.node)

        context['utilization_rows'] = []
        for tree in trees:
            context['utilization_rows'] += [
                {'link': link, 'root_nodes': [tree.root_node]}
                for link in tree.get_links_using_node(self.node)
            ]
        context['utilization_rows'] = sorted(context['utilization_rows'], key=lambda row: row['link'].parent.code)
        return context


class EducationGroupYearAdmissionCondition(EducationGroupGenericDetailView):
    template_name = "education_group/tab_admission_conditions.html"

    def can_show_view(self):
        return self.show_admission_conditions()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tab_lang = cache.get(get_tab_lang_keys(self.request.user)) or settings.LANGUAGE_CODE_FR

        acronym = self.object.acronym.lower()
        is_common = acronym.startswith('common-')
        is_specific = not is_common
        is_bachelor = self.object.is_bachelor

        is_master = acronym.endswith(('2m', '2m1'))
        is_aggregation = acronym.endswith('2a')
        is_mc = acronym.endswith('2mc')
        common_conditions = get_appropriate_common_admission_condition(self.object)

        class AdmissionConditionForm(forms.Form):
            text_field = forms.CharField(widget=CKEditorWidget(config_name='education_group_pedagogy'))

        admission_condition_form = AdmissionConditionForm()
        admission_condition, created = AdmissionCondition.objects.get_or_create(education_group_year=self.object)
        record = {}
        for section in SECTIONS_WITH_TEXT:
            record[section] = AdmissionConditionLine.objects.filter(
                admission_condition=admission_condition,
                section=section
            ).annotate_text(tab_lang)
        perm_name = 'base.change_commonadmissioncondition' if is_common else 'base.change_admissioncondition'
        context.update({
            'admission_condition_form': admission_condition_form,
            'can_edit_information': self.request.user.has_perm(perm_name, self.object),
            'info': {
                'is_specific': is_specific,
                'is_common': is_common,
                'is_bachelor': is_bachelor,
                'is_master': is_master,
                'show_components_for_agreg': is_aggregation,
                'show_components_for_agreg_and_mc': is_aggregation or is_mc,
                'show_free_text': self._show_free_text()
            },
            'admission_condition': admission_condition,
            'common_conditions': common_conditions,
            'record': record,
            'language': {
                'list': ["fr-be", "en"],
                'tab_lang': tab_lang
            }
        })

        return context

    def _show_free_text(self):
        concerned_training_types = list(TrainingType.with_admission_condition())
        return not self.object.is_common and self.object.education_group_type.name in itertools.chain(
            concerned_training_types,
            MiniTrainingType.with_admission_condition(),
        )


def get_appropriate_common_admission_condition(edy):
    if not edy.is_common and any([
        edy.is_bachelor,
        edy.is_master60,
        edy.is_master120,
        edy.is_aggregation,
        edy.is_specialized_master,
        edy.is_master180
    ]):
        common_egy = EducationGroupYear.objects.look_for_common(
            education_group_type__name=TrainingType.PGRM_MASTER_120.name if edy.is_master60 or edy.is_master180
            else edy.education_group_type.name,
            academic_year=edy.academic_year
        ).get()
        common_admission_condition, created = AdmissionCondition.objects.get_or_create(education_group_year=common_egy)
        return common_admission_condition
    return None
