/* OSIS stands for Open Student Information System. It's an application
* designed to manage the core business of higher education institutions,
* such as universities, faculties, institutes and professional schools.
* The core business involves the administration of students, teachers,
* courses, programs and so on.
*
* Copyright (C) 2017-2018 Université catholique de Louvain (http://www.uclouvain.be)
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* A copy of this license - GNU General Public License - is available
* at the root of the source code of this program.  If not,
* see http://www.gnu.org/licenses/.
*
* OSIS Custom layout
*/

    $( document ).ready(function() {
        $("input[type=checkbox]")
        .each(function() {
            if (this.name.indexOf('txt_checkbox_')!=-1 && this.checked)
            {
                this.click();
                this.click();
            }
        })
    });

    function display_hide_div_child(id_div_child,id_statut_bouton)
    {
        var div_child = document.getElementById(id_div_child);
        var statut_bouton = document.getElementById(id_statut_bouton);
             if(statut_bouton.value == "OK" && (div_child.style.display!="none") )
             {
                div_child.style.display = "none";
             }else
             {
                div_child.style.display = "BLOCK";
             }
    }

    function block_div(check_box,id_div_kinsman,id_statut_bouton,id_div_child)
    {
        var statut_bouton = document.getElementById(id_statut_bouton);
        var div_kinsman= document.getElementById(id_div_kinsman);
        var div_child = document.getElementById(id_div_child);
        if (check_box.checked)
        {
            div_child.style.display = "block";
            statut_bouton.value ="KO";
        }
    }
