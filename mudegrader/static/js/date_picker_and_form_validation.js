document.addEventListener('DOMContentLoaded', function () {
    flatpickr(".flatpickr", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
    });

    // Function to validate form
    function validateForm() {
        const title = document.getElementById('id_title').value;
        const dueDate = document.getElementById('id_due_date').value;
        const description = document.getElementById('id_description').value;
        const totalPoints = document.getElementById('id_total_points').value;
        const isIndividual = document.getElementById('id_is_individual').checked;

        return title && dueDate && description && totalPoints && isIndividual;
    }

    // Function to toggle the upload button
    // function toggleUploadButton() {
    //     const uploadZipButton = document.getElementById('uploadZipButton');
    //     if (validateForm()) {
    //         uploadZipButton.removeAttribute('disabled');
    //     } else {
    //         uploadZipButton.setAttribute('disabled', 'disabled');
    //     }
    // }

    // // Adding event listeners to form fields
    // document.querySelectorAll('#id_title, #id_due_date, #id_description, #id_total_points, #id_is_individual').forEach(input => {
    //     input.addEventListener('input', toggleUploadButton);
    //     input.addEventListener('change', toggleUploadButton);
    // });

    toggleUploadButton(); // Initial check to disable or enable the button
});
