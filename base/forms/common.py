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
from django.utils.safestring import mark_safe


def get_clean_data(datas_to_clean):
    return {key: treat_empty_or_str_none_as_none(value) for (key, value) in datas_to_clean.items()}


def treat_empty_or_str_none_as_none(data):
    return None if not data or data == "NONE" else data


class TooManyResultsException(Exception):
    def __init__(self):
        super().__init__("Too many results returned.")


def set_trans_txt(form, texts_list):
    for trans_txt in texts_list:
        text_label = trans_txt.text_label.label
        text = trans_txt.text if trans_txt.text else ""
        setattr(form, text_label, mark_safe(text))
