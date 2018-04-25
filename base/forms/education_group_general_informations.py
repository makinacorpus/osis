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
from django import forms
from django.utils.safestring import mark_safe
from ckeditor.widgets import CKEditorWidget

from base.forms.common import set_trans_txt
from cms.enums import entity_name
from cms.models import translated_text
from cms import models as mdl_cms


class EducationGroupGeneralInformationsForm(forms.Form):
    education_group_year = language = None
    text_labels_name = None

    def __init__(self, *args, **kwargs):
        self.education_group_year = kwargs.pop('education_group_year', None)
        self.language = kwargs.pop('language', None)
        self.text_labels_name = kwargs.pop('text_labels_name', None)
        self.load_initial()
        super().__init__(*args, **kwargs)

    def load_initial(self):
        translated_texts_list = self._get_all_translated_text_related()
        set_trans_txt(self, translated_texts_list)

    def _get_all_translated_text_related(self):
        language_iso = self.language[0]
        return translated_text.search(entity=entity_name.OFFER_YEAR,
                                      reference=self.education_group_year.id,
                                      language=language_iso,
                                      text_labels_name=self.text_labels_name)
