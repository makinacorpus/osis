 $(".pedagogy-edit-btn").click(function(ev) {
            ev.preventDefault();
            var url = $(this).data("form"); // get the contact form url
            var pedagogy_edit_modal = $("#pedagogy_edit");
            pedagogy_edit_modal.load(url, function() { // load the url into the modal
                $(this).modal('show');
            });
            return false;
        });