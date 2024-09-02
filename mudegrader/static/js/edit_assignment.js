document.addEventListener('DOMContentLoaded', function () {
    flatpickr(".flatpickr", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
    });


    const elements = ['id_title', 'id_due_date', 'id_description', 'id_total_points', 'id_is_individual'];
        // elements.forEach(el => {
        //     document.getElementById(el).addEventListener('input', toggleUploadButton);
        //     document.getElementById(el).addEventListener('change', toggleUploadButton);
        // });
    // Function to validate form
    function validateForm() {
        const title = document.getElementById('id_title').value;
        // const dueDate = document.getElementById('id_due_date').value;
        // const description = document.getElementById('id_description').value;
        const totalPoints = document.getElementById('id_total_points').value;

        // return title && dueDate && description && totalPoints;
        return title && totalPoints;
    }

    // function toggleUploadButton() {
    //     const uploadZipButton = document.getElementById('uploadZipButton');
    //     if (validateForm()) {
    //         uploadZipButton.removeAttribute('disabled');
    //     } else {
    //         uploadZipButton.setAttribute('disabled', 'disabled');
    //     }
    // }


    var iframe = document.getElementById('fileViewerIframe');
    var previewDiv = document.getElementById('filePreviewDiv');
    var previewUrl = '';
    var previewContent = '';
    var isMarkdown = false;
    var jupyterLabToken = 'my_fixed_token123';

    function attachIconEvents() {
        document.querySelectorAll('.view-icon').forEach(function (icon) {
            icon.addEventListener('click', function (event) {
                var url = '/project_files' + event.target.closest('.view-icon').dataset.url;
                var extension = event.target.closest('.view-icon').dataset.extension;
                handleFileView(url, extension);
            });
        });

        document.querySelectorAll('.edit-icon').forEach(function (icon) {
            icon.addEventListener('click', function (event) {
                var url = '/project_files' + event.target.closest('.edit-icon').dataset.url;
                var extension = event.target.closest('.edit-icon').dataset.extension;
                handleFileEdit(url, extension);
            });
        });

        document.querySelectorAll('.download-icon').forEach(function (icon) {
            icon.addEventListener('click', function (event) {
                var url = '/project_files' + event.target.closest('.download-icon').dataset.url;
                handleFileDownload(url);
            });
        });
    }

    function handleFileView(url, extension) {
        if (['pdf', 'html'].includes(extension)) {
            iframe.src = url;
            iframe.style.display = 'block';
            previewDiv.style.display = 'none';
            previewUrl = url;
        } else if (['md', 'markdown'].includes(extension)) {
            fetch(url)
                .then(response => response.text())
                .then(data => {
                    var converter = new showdown.Converter();
                    var html = converter.makeHtml(data);
                    previewDiv.innerHTML = html;
                    previewDiv.style.display = 'block';
                    iframe.style.display = 'none';
                    previewUrl = url;
                    previewContent = html;
                    isMarkdown = true;
                })
                .catch(error => console.error('Error loading Markdown file:', error));
        } else if (['ipynb'].includes(extension)) {
            var jupyterLabBaseUrl = 'http://localhost/jupyter/lab';
            var constructedUrl = `${jupyterLabBaseUrl}/tree/${url.replace('/project_files/assignments', '')}?token=${jupyterLabToken}`;
            iframe.src = constructedUrl;
            iframe.style.display = 'block';
            previewDiv.style.display = 'none';
            previewUrl = constructedUrl;
        } else {
            iframe.src = url;
            iframe.style.display = 'block';
            previewDiv.style.display = 'none';
            previewUrl = url;
        }
    }

    function handleFileEdit(url, extension) {
        if (['ipynb', 'md', 'markdown', 'txt'].includes(extension)) {
            var jupyterLabBaseUrl = 'http://localhost/jupyter/lab';
            var constructedUrl = `${jupyterLabBaseUrl}/lab/tree/${url.replace('/project_files/assignments', '')}?token=${jupyterLabToken}`;
            iframe.src = constructedUrl;
            iframe.style.display = 'block';
            previewDiv.style.display = 'none';
            previewUrl = constructedUrl;
        } else {
            iframe.src = url;
            iframe.style.display = 'block';
            previewDiv.style.display = 'none';
            previewUrl = url;
        }
    }

    function handleFileDownload(url) {
        var downloadUrl = url;
        window.open(downloadUrl, '_blank');
    }

    var fullScreenButton = document.getElementById('fullScreenButton');
    fullScreenButton.addEventListener('click', function () {
        if (previewUrl) {
            if (isMarkdown) {
                var newWindow = window.open('', '_blank');
                newWindow.document.write('<html><head><title>Markdown Preview</title></head><body>');
                newWindow.document.write(previewContent);
                newWindow.document.write('</body></html>');
                newWindow.document.close();
            } else {
                window.open(previewUrl, '_blank');
            }
        } else {
            alert('No file is currently being previewed.');
        }
    });

    function updateIcons(url, extension) {
        var viewIcon = document.querySelector('.view-icon');
        var editIcon = document.querySelector('.edit-icon');
        var downloadIcon = document.querySelector('.download-icon');

        viewIcon.dataset.url = url;
        viewIcon.dataset.extension = extension;
        editIcon.dataset.url = url;
        editIcon.dataset.extension = extension;
        downloadIcon.dataset.url = url;

        document.querySelector('.file-icons').style.display = 'block';
    }

    function addFileLinksEventListeners() {
        document.querySelectorAll('.file-link').forEach(function (link) {
            link.addEventListener('click', function (event) {
                event.preventDefault();
                var url = '/project_files' + link.dataset.url;
                var extension = link.dataset.extension;
                updateIcons(url, extension);
                handleFileView(url, extension);
            });
        });
    }


    function updateTasks(assignmentUnitIndex, numberOfTasks) {
        var tasksContainer = document.getElementById(`tasks-container-${assignmentUnitIndex}`);
        tasksContainer.innerHTML = '';

        for (var i = 0; i < numberOfTasks; i++) {
            var taskDiv = document.createElement('div');
            taskDiv.classList.add('task');

            var taskLabel = document.createElement('label');
            taskLabel.textContent = `Task ${i + 1}:`;
            taskDiv.appendChild(taskLabel);

            var taskMaxScoreInput = document.createElement('input');
            taskMaxScoreInput.setAttribute('type', 'number');
            taskMaxScoreInput.setAttribute('name', `units-${assignmentUnitIndex}-tasks-${i}-max_score`);
            taskMaxScoreInput.setAttribute('placeholder', 'Max Score');
            taskDiv.appendChild(taskMaxScoreInput);

            var taskIsAutoGradedCheckbox = document.createElement('input');
            taskIsAutoGradedCheckbox.setAttribute('type', 'checkbox');
            taskIsAutoGradedCheckbox.setAttribute('name', `units-${assignmentUnitIndex}-tasks-${i}-is_auto_graded`);
            taskIsAutoGradedCheckbox.setAttribute('value', 'true');
            if (document.querySelector(`input[name="units-${assignmentUnitIndex}-tasks-${i}-is_auto_graded"]`)?.checked) {
                taskIsAutoGradedCheckbox.checked = true;
            }

            var taskIsAutoGradedLabel = document.createElement('label');
            taskIsAutoGradedLabel.textContent = 'Auto Graded';
            taskIsAutoGradedLabel.appendChild(taskIsAutoGradedCheckbox);
            taskDiv.appendChild(taskIsAutoGradedLabel);

            tasksContainer.appendChild(taskDiv);
        }
    }


    var deleteButtons = document.querySelectorAll('.deleteAssignmentUnitButton');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            var unitId = event.target.dataset.unitId;
            var confirmed = confirm('Are you sure you want to delete this file?');
            if (confirmed) {
                fetch(`{% url 'delete_assignment_unit' 0 %}`.replace('0', unitId), {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': '{{ csrf_token }}'
                    }
                }).then(response => {
                    if (response.ok) {
                        event.target.closest('.assignmentUnit').remove();
                    } else {
                        alert('Failed to delete the file.');
                    }
                });
            }
        });
    });

    addSlugValidation('id_title');
    attachIconEvents();
    addFileLinksEventListeners();

    // Upload ZIP file event listener
    document.getElementById('uploadZipButton').addEventListener('click', function () {
        if (validateForm()) {
            const modal = document.getElementById('importZipModal');
            modal.style.display = 'block';
        } else {
            alert('Please fill out all required fields before uploading.');
        }
    });


    // Initialize tasks for existing units without overriding existing values
    document.querySelectorAll('.assignmentUnit').forEach(function(unit, index) {
        const numberOfTasksInput = unit.querySelector('input[name$="-number_of_tasks"]');
        numberOfTasksInput.addEventListener('input', function () {
            if (this.dataset.initialized !== 'true') {
                this.dataset.initialized = 'true';
            } else {
                updateTasks(index, numberOfTasksInput.value);
            }
        });
    });
});
