# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-31 13:01
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0481_auto_20191106_1539'),
    ]

    operations = [
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
             ['{% autoescape off %}\r\n<p>Bonjour,</p>\r\n<p>Ceci est un message automatique g\u00e9n\u00e9r\u00e9 par le serveur OSIS – Merci de ne pas y r\u00e9pondre.</p>\r\n<p>Lancement de la proc\u00e9dure annuelle de copie des unit\u00e9s d’enseignement pour l\u0027ann\u00e9e acad\u00e9mique {{ end_academic_year }}.</p>\r\n<p><b>Merci de noter que les unit\u00e9s d\u0027enseignement externes de mobilit\u00e9 ne sont pas concern\u00e9es.</b></p>\r\n<p>{{ luys_to_postpone }} UE à copier de {{ academic_year }} en {{ end_academic_year }}.</p>\r\n<p>{{ luys_ending_this_year }} UE avec une fin d\u0027enseignement en {{ academic_year }}.</p>\r\n<p>{{ luys_already_existing }} UE existant pr\u00e9alablement en {{ end_academic_year }}.</p><p>\r\nCordialement,\r\nOsis UCLouvain</p>\r\n{% endautoescape %}',
              'luy_before_auto_postponement_html',
              'HTML',
              'fr-be'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
             ['<p>Bonjour,</p>\r\n<p>Ceci est un message automatique g\u00e9n\u00e9r\u00e9 par le serveur OSIS – Merci de ne pas y r\u00e9pondre.</p>\r\n<p>Lancement de la proc\u00e9dure annuelle de copie des unit\u00e9s d’enseignement pour l\u0027ann\u00e9e acad\u00e9mique {{ end_academic_year }}.</p>\r\n<p>Merci de noter que les unit\u00e9s d\u0027enseignement externes de mobilit\u00e9 ne sont pas concern\u00e9es.</p>\r\n<p>{{ luys_to_postpone }} UE à copier de {{ academic_year }} en {{ end_academic_year }}.</p>\r\n<p>{{ luys_ending_this_year }} UE avec une fin d\u0027enseignement en {{ academic_year }}.</p>\r\n<p>{{ luys_already_existing }} UE existant pr\u00e9alablement en {{ end_academic_year }}.</p><p>\r\nCordialement,\r\nOsis UCLouvain</p>\r\n',
              'luy_before_auto_postponement_txt',
              'PLAIN',
              'fr-be'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
             ['{% autoescape off %}\r\n<p>Hello,</p>\r\n<p>This is an automatic message generated by the OSIS server – Please do not reply to this message.</p>\r\n<p>Initiation of the annual procedure of copy of the learning units for the academic year {{ end_academic_year }}.</p>\r\n<p><b>Please note external learning units with mobility are not considered.</b></p>\r\n<p>{{ luys_to_postpone }} LU to copy from {{ academic_year }} to {{ end_academic_year }}.</p>\r\n<p>{{ luys_ending_this_year }} LU ending in {{ academic_year }}.</p>\r\n<p>{{ luys_already_existing }} LU already existing in {{ end_academic_year }}.</p><p>\r\nRegards,\r\nOsis UCLouvain</p>\r\n{% endautoescape off %}',
              'luy_before_auto_postponement_html',
              'HTML',
              'en'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
             ['<p>Hello,</p>\r\n<p>This is an automatic message generated by the OSIS server – Please do not reply to this message.</p>\r\n<p>Initiation of the annual procedure of copy of the learning units for the academic year {{ end_academic_year }}.</p>\r\n<p>Please note external learning units with mobility are not considered.</p>\r\n<p>{{ luys_to_postpone }} LU to copy from {{ academic_year }} to {{ end_academic_year }}.</p>\r\n<p>{{ luys_ending_this_year }} LU ending in {{ academic_year }}.</p>\r\n<p>{{ luys_ending_this_year }} LU ending in {{ academic_year }}.</p>\r\n<p>{{ luys_already_existing }} LU already existing in {{ end_academic_year }}.</p><p>\r\nRegards,\r\nOsis UCLouvain</p>\r\n',
              'luy_before_auto_postponement_txt',
              'PLAIN',
              'en'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
              ['{% autoescape off %}\r\n<p>Bonjour,</p>\r\n<p>Ceci est un message automatique g\u00e9n\u00e9r\u00e9 par le serveur OSIS – Merci de ne pas y r\u00e9pondre.</p>\r\n<p>Lancement de la proc\u00e9dure annuelle de copie des organisations de formation pour l\u0027ann\u00e9e acad\u00e9mique {{ current_academic_year }}.</p>\r\n<p>{{ egys_to_postpone }} OF à copier de {{ previous_academic_year }} en {{ current_academic_year }}.</p>\r\n<p>{{ egys_ending_this_year }} OF avec une fin d\u0027enseignement en {{ current_academic_year }}.</p>\r\n<p>{{ egys_already_existing }} OF existant pr\u00e9alablement en {{ previous_academic_year }}.</p><p>\r\nCordialement,\r\nOsis UCLouvain</p>\r\n{% endautoescape %}',
               'egy_before_auto_postponement_html',
               'HTML',
               'fr-be'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
              ['<p>Bonjour,</p>\r\n<p>Ceci est un message automatique g\u00e9n\u00e9r\u00e9 par le serveur OSIS – Merci de ne pas y r\u00e9pondre.</p>\r\n<p>Lancement de la proc\u00e9dure annuelle de copie des organisations de formation pour l\u0027ann\u00e9e acad\u00e9mique {{ current_academic_year }}.</p>\r\n<p>{{ egys_to_postpone }} OF à copier de {{ previous_academic_year }} en {{ current_academic_year }}.</p>\r\n<p>{{ egys_ending_this_year }} OF avec une fin d\u0027enseignement en {{ current_academic_year }}.</p>\r\n<p>{{ egys_already_existing }} OF existant pr\u00e9alablement en {{ previous_academic_year }}.</p><p>\r\nCordialement,\r\nOsis UCLouvain</p>\r\n',
               'egy_before_auto_postponement_txt',
               'PLAIN',
               'fr-be'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
              ['{% autoescape off %}\r\n<p>Hello,</p>\r\n<p>This is an automatic message generated by the OSIS server – Please do not reply to this message.</p>\r\n<p>Initiation of the annual procedure of copy of the education groups for the academic year {{ current_academic_year }}.</p>\r\n<p>{{ egys_to_postpone }} EG to copy from {{ previous_academic_year }} to {{ current_academic_year }}.</p>\r\n<p>{{ egys_ending_this_year }} EG ending in {{ current_academic_year }}.</p>\r\n<p>{{ egys_already_existing }} EG already existing in {{ previous_academic_year }}.</p><p>\r\nRegards,\r\nOsis UCLouvain</p>\r\n{% endautoescape off %}',
               'egy_before_auto_postponement_html',
               'HTML',
               'en'])],
        ),
        migrations.RunSQL(
            [("UPDATE osis_common_messagetemplate SET template=%s WHERE reference=%s AND format=%s AND language=%s;",
              ['<p>Hello,</p>\r\n<p>This is an automatic message generated by the OSIS server – Please do not reply to this message.</p>\r\n<p>Initiation of the annual procedure of copy of the education groups for the academic year {{ current_academic_year }}.</p>\r\n<p>{{ egys_to_postpone }} EG to copy from {{ previous_academic_year }} to {{ current_academic_year }}.</p>\r\n<p>{{ egys_ending_this_year }} EG ending in {{ current_academic_year }}.</p>\r\n<p>{{ egys_already_existing }} EG already existing in {{ previous_academic_year }}.</p><p>\r\nRegards,\r\nOsis UCLouvain</p>\r\n',
               'egy_before_auto_postponement_txt',
               'PLAIN',
               'en'])],
        ),
    ]
