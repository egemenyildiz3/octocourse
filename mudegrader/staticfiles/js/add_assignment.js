document.addEventListener('DOMContentLoaded', () => {
    flatpickr(".flatpickr", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
    });

    addSlugValidation('id_title');

    const elements = ['id_title', 'id_due_date', 'id_description', 'id_total_points', 'id_is_individual'];
    // elements.forEach(el => {
    //     document.getElementById(el).addEventListener('input', toggleUploadButton);
    //     document.getElementById(el).addEventListener('change', toggleUploadButton);
    // });

    // toggleUploadButton();

    function addSlugValidation(id) {
        // Slug validation code here
    }

    function validateForm() {
        const title = document.getElementById('id_title').value;
        const dueDate = document.getElementById('id_due_date').value;
        const description = document.getElementById('id_description').value;
        const totalPoints = document.getElementById('id_total_points').value;

        return title && dueDate && description && totalPoints && isIndividual;
    }

    function toggleUploadButton() {
        const uploadZipButton = document.getElementById('uploadZipButton');
        if (validateForm()) {
            uploadZipButton.removeAttribute('disabled');
        } else {
            uploadZipButton.setAttribute('disabled', 'disabled');
        }
    }

    const addAssignmentUnitButton = document.getElementById('addAssignmentUnitButton');
    const assignmentUnitsContainer = document.getElementById('assignmentUnitsContainer');

    function addAssignmentUnit() {
        const assignmentUnitIndex = document.querySelectorAll('.assignmentUnit').length;
        const assignmentUnit = document.createElement('div');
        assignmentUnit.classList.add('assignmentUnit');

        const fileInput = document.createElement('input');
        fileInput.setAttribute('type', 'file');
        fileInput.setAttribute('name', `units-${assignmentUnitIndex}-file`);
        fileInput.addEventListener('change', function () {
            const fileName = fileInput.files[0].name;
            assignmentUnit.querySelector('.file-name').textContent = fileName;
            assignmentUnit.querySelector('input[name^="units-"][name$="-name"]').value = fileName;  // Set the hidden name input
        });
        assignmentUnit.appendChild(fileInput);

        const fileNameLabel = document.createElement('div');
        fileNameLabel.classList.add('file-name');
        assignmentUnit.appendChild(fileNameLabel);

        const nameInput = document.createElement('input');
        nameInput.setAttribute('type', 'hidden');  // Hidden input to store the file name
        nameInput.setAttribute('name', `units-${assignmentUnitIndex}-name`);
        assignmentUnit.appendChild(nameInput);

        const typeSelect = document.createElement('select');
        typeSelect.setAttribute('name', `units-${assignmentUnitIndex}-type`);
        const masterOption = document.createElement('option');
        masterOption.setAttribute('value', 'master');
        masterOption.textContent = 'Auto-graded Notebook ';
        typeSelect.appendChild(masterOption);
        const nonMasterOption = document.createElement('option');
        nonMasterOption.setAttribute('value', 'non_master');
        nonMasterOption.textContent = 'Manually Notebook';
        typeSelect.appendChild(nonMasterOption);
        assignmentUnit.appendChild(typeSelect);

        const totalPointsInput = document.createElement('input');
        totalPointsInput.setAttribute('type', 'number');
        totalPointsInput.setAttribute('name', `units-${assignmentUnitIndex}-total_points`);
        totalPointsInput.setAttribute('placeholder', 'Total Points');
        assignmentUnit.appendChild(totalPointsInput);

        const numberOfTasksInput = document.createElement('input');
        numberOfTasksInput.setAttribute('type', 'number');
        numberOfTasksInput.setAttribute('name', `units-${assignmentUnitIndex}-number_of_tasks`);
        numberOfTasksInput.setAttribute('placeholder', 'Number of Tasks');
        numberOfTasksInput.addEventListener('input', function () {
            updateTasks(assignmentUnitIndex, numberOfTasksInput.value);
        });
        assignmentUnit.appendChild(numberOfTasksInput);

        const isGradedCheckbox = document.createElement('input');
        isGradedCheckbox.setAttribute('type', 'checkbox');
        isGradedCheckbox.setAttribute('name', `units-${assignmentUnitIndex}-is_graded`);
        isGradedCheckbox.setAttribute('value', 'true');
        assignmentUnit.appendChild(isGradedCheckbox);

        const tasksContainer = document.createElement('div');
        tasksContainer.classList.add('tasks');
        tasksContainer.setAttribute('id', `tasks-container-${assignmentUnitIndex}`);
        assignmentUnit.appendChild(tasksContainer);

        const deleteButton = document.createElement('button');
        deleteButton.setAttribute('type', 'button');
        deleteButton.textContent = 'Delete';
        deleteButton.classList.add('deleteAssignmentUnitButton');
        deleteButton.addEventListener('click', function () {
            assignmentUnit.remove();
        });
        assignmentUnit.appendChild(deleteButton);

        assignmentUnitsContainer.appendChild(assignmentUnit);
    }

    if (addAssignmentUnitButton) {
        addAssignmentUnitButton.addEventListener('click', addAssignmentUnit);
    }

    function updateTasks(assignmentUnitIndex, numberOfTasks) {
        const tasksContainer = document.getElementById(`tasks-container-${assignmentUnitIndex}`);
        tasksContainer.innerHTML = '';

        for (let i = 0; i < numberOfTasks; i++) {
            const taskDiv = document.createElement('div');
            taskDiv.classList.add('task');

            const taskLabel = document.createElement('label');
            taskLabel.textContent = `Task ${i + 1}:`;
            taskDiv.appendChild(taskLabel);

            const taskMaxScoreInput = document.createElement('input');
            taskMaxScoreInput.setAttribute('type', 'number');
            taskMaxScoreInput.setAttribute('name', `units-${assignmentUnitIndex}-tasks-${i}-max_score`);
            taskMaxScoreInput.setAttribute('placeholder', 'Max Score');
            taskDiv.appendChild(taskMaxScoreInput);

            const taskIsAutoGradedCheckbox = document.createElement('input');
            taskIsAutoGradedCheckbox.setAttribute('type', 'checkbox');
            taskIsAutoGradedCheckbox.setAttribute('name', `units-${assignmentUnitIndex}-tasks-${i}-is_auto_graded`);
            taskIsAutoGradedCheckbox.setAttribute('value', 'true');

            const taskIsAutoGradedLabel = document.createElement('label');
            taskIsAutoGradedLabel.textContent = 'Auto Graded';
            taskIsAutoGradedLabel.appendChild(taskIsAutoGradedCheckbox);
            taskDiv.appendChild(taskIsAutoGradedLabel);

            tasksContainer.appendChild(taskDiv);
        }
    }
});
