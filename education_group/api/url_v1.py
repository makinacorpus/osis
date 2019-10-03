##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf.urls import url

from education_group.api.views.group_element_year import TrainingTreeView, GroupTreeView, MiniTrainingTreeView
from education_group.api.views.group import GroupDetail
from education_group.api.views.mini_training import MiniTrainingDetail
from education_group.api.views.training import TrainingList, TrainingDetail

app_name = "education_group"

# FIXME: Refactor URL
urlpatterns = [
    url(r'^trainings$', TrainingList.as_view(), name=TrainingList.name),
    url(
        r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/]?[a-zA-Z]{1,2})?)$',
        TrainingDetail.as_view(),
        name=TrainingDetail.name
    ),
    url(
        r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/]?[a-zA-Z]{1,2})?)/tree$',
        TrainingTreeView.as_view(),
        name=TrainingTreeView.name
    ),
    url(
        r'^mini_trainings/(?P<year>[\d]{4})/(?P<partial_acronym>[\w]+)$',
        MiniTrainingDetail.as_view(),
        name=MiniTrainingDetail.name
    ),
    url(
        r'^mini_trainings/(?P<year>[0-9]{4})/(?P<partial_acronym>[a-zA-Z0-9]+)/tree$',
        MiniTrainingTreeView.as_view(),
        name=MiniTrainingTreeView.name
    ),
    url(
        r'^groups/(?P<year>[\d]{4})/(?P<partial_acronym>[\w]+)$',
        GroupDetail.as_view(),
        name=GroupDetail.name
    ),
    url(
        r'^groups/(?P<year>[0-9]{4})/(?P<partial_acronym>[a-zA-Z0-9]+)/tree$',
        GroupTreeView.as_view(),
        name=GroupTreeView.name
    ),
]
