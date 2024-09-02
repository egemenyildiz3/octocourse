document.addEventListener('DOMContentLoaded', function () {
    function addSlugValidation(fieldId) {
        const field = document.getElementById(fieldId);
        field.addEventListener('input', function () {
            field.value = field.value.replace(/\s+/g, '-').toLowerCase();
        });
    }


    // Download assignment as ZIP event listener
    document.getElementById('downloadAssignmentButton').addEventListener('click', function () {
        const assignmentId = document.getElementById('assignmentForm').dataset.assignmentId;
        if (assignmentId) {
            window.location.href = `/assignments/download/${assignmentId}/`;
        } else {
            alert('Assignment ID not found.');
        }
    });

    addSlugValidation('id_title');
});
