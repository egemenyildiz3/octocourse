document.addEventListener('DOMContentLoaded', function () {
    function addAssignmentUnit() {
        var assignmentUnitIndex = document.querySelectorAll('.assignmentUnit').length;
        var assignmentUnit = document.createElement('div');
        assignmentUnit.classList.add('assignmentUnit');

        var nameInput = document.createElement('input');
        nameInput.setAttribute('type', 'text');
        nameInput.setAttribute('name', `units-${assignmentUnitIndex}-name`);
        nameInput.setAttribute('placeholder', 'File Name');
        assignmentUnit.appendChild(nameInput);

        var fileInput = document.createElement('input');
        fileInput.setAttribute('type', 'file');
        fileInput.setAttribute('name', `units-${assignmentUnitIndex}-file`);
        assignmentUnit.appendChild(fileInput);

        var typeSelect = document.createElement('select');
        typeSelect.setAttribute('name', `units-${assignmentUnitIndex}-type`);
        var masterOption = document.createElement('option');
        masterOption.setAttribute('value', 'master');
        masterOption.textContent = 'Auto-graded Notebook ';
        typeSelect.appendChild(masterOption);
        var nonMasterOption = document.createElement('option');
        nonMasterOption.setAttribute('value', 'non_master');
        nonMasterOption.textContent = 'Manually Notebook';
        typeSelect.appendChild(nonMasterOption);
        assignmentUnit.appendChild(typeSelect);

        var totalPointsInput = document.createElement('input');
        totalPointsInput.setAttribute('type', 'number');
        totalPointsInput.setAttribute('name', `units-${assignmentUnitIndex}-total_points`);
        totalPointsInput.setAttribute('placeholder', 'Total Points');
        assignmentUnit.appendChild(totalPointsInput);

        var numberOfTasksInput = document.createElement('input');
        numberOfTasksInput.setAttribute('type', 'number');
        numberOfTasksInput.setAttribute('name', `units-${assignmentUnitIndex}-number_of_tasks`);
        numberOfTasksInput.setAttribute('placeholder', 'Number of Tasks');
        numberOfTasksInput.addEventListener('input', function () {
            updateTasks(assignmentUnitIndex, numberOfTasksInput.value);
        });
        assignmentUnit.appendChild(numberOfTasksInput);

        var isGradedCheckbox = document.createElement('input');
        isGradedCheckbox.setAttribute('type', 'checkbox');
        isGradedCheckbox.setAttribute('name', `units-${assignmentUnitIndex}-is_graded`);
        isGradedCheckbox.setAttribute('value', 'true');
        assignmentUnit.appendChild(isGradedCheckbox);

        var tasksContainer = document.createElement('div');
        tasksContainer.classList.add('tasks');
        tasksContainer.setAttribute('id', `tasks-container-${assignmentUnitIndex}`);
        assignmentUnit.appendChild(tasksContainer);

        var deleteButton = document.createElement('button');
        deleteButton.setAttribute('type', 'button');
        deleteButton.textContent = 'Delete';
        deleteButton.classList.add('deleteAssignmentUnitButton');
        deleteButton.addEventListener('click', function () {
            assignmentUnit.remove();
        });
        assignmentUnit.appendChild(deleteButton);

        assignmentUnitsContainer.appendChild(assignmentUnit);
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

            tasksContainer.appendChild(taskDiv);
        }
    }

    var addAssignmentUnitButton = document.getElementById('addAssignmentUnitButton');
    var assignmentUnitsContainer = document.getElementById('assignmentUnitsContainer');

    addAssignmentUnitButton.addEventListener('click', function () {
        addAssignmentUnit();
    });

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

    // Additional functions for managing assignment units can go here
});
