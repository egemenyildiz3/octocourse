document.addEventListener("DOMContentLoaded", function() {
    const modal = document.getElementById('importZipModal');
    const closeButton = modal.querySelector('.close');
    const importBtn = document.getElementById('uploadZipButton');
    const dropZone = document.getElementById('drop_zone_zip');
    const fileInput = document.getElementById('fileInputZip');
    const uploadButton = document.getElementById('uploadButtonZip');
    const addAssignmentUnitButton = document.getElementById('addAssignmentUnitButton');
    const assignmentUnitsContainer = document.getElementById('assignmentUnitsContainer');
    const createButton = document.querySelector('button[type="submit"]');
    let zipFormData = new FormData();

    modal.style.display = 'none';

    importBtn.addEventListener('click', function() {
        console.log("Opening modal");
        modal.style.display = 'block';
    });

    closeButton.addEventListener('click', function() {
        console.log("Closing modal");
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            console.log("Closing modal by clicking outside");
            modal.style.display = 'none';
        }
    });

    dropZone.addEventListener('dragover', function(event) {
        event.preventDefault();
        dropZone.style.backgroundColor = '#f0f0f0';
    });

    dropZone.addEventListener('dragleave', function(event) {
        event.preventDefault();
        dropZone.style.backgroundColor = '';
    });

    dropZone.addEventListener('drop', function(event) {
        event.preventDefault();
        dropZone.style.backgroundColor = '';
        console.log("File dropped");
        fileChangeHandler(event.dataTransfer.files);
    });

    fileInput.addEventListener('change', function() {
        console.log("File selected");
        fileChangeHandler(this.files);
    });

    uploadButton.addEventListener('click', function() {
        console.log("Upload button clicked");
        createAssignmentAndUploadFiles(true);  // true indicates ZIP file upload
    });

    createButton.addEventListener('click', function(event) {
        event.preventDefault();
        console.log("Create button clicked");
        createAssignmentAndUploadFiles(false);  // false indicates normal assignment creation
    });

    function fileChangeHandler(files) {
        const fileListDisplay = document.getElementById('fileListZip');
        fileListDisplay.innerHTML = '';
        zipFormData = new FormData();

        for (let i = 0; i < files.length; i++) {
            zipFormData.append('file', files[i]);
            console.log(`Added file to FormData: ${files[i].name}`);

            const fileEntry = document.createElement('div');
            fileEntry.textContent = files[i].name;
            fileEntry.style.color = '#4CAF50';
            fileListDisplay.appendChild(fileEntry);
        }
    }

    async function createAssignmentAndUploadFiles(isZipUpload) {
        const assignmentForm = document.getElementById('assignmentForm');
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
        const assignmentFormData = new FormData(assignmentForm);
    
        try {
            const response = await fetch(assignmentForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest' // Ensure the request is recognized as AJAX
                },
                body: assignmentFormData,
                credentials: 'include'
            });
    
            const data = await response.json();
    
            if (response.ok || response.redirected) {
                const assignmentId = data.assignment_id;
                console.log("Created assignment with ID:", assignmentId);
    
                if (isZipUpload) {
                    console.log(`Sending ZIP file to /assignments/import_zip/${assignmentId}/`);
    
                    const zipResponse = await fetch(`/assignments/import_zip/${assignmentId}/`, {
                        method: 'POST',
                        body: zipFormData,
                        credentials: 'include'
                    });
    
                    if (zipResponse.redirected) {
                        window.location.href = zipResponse.url;
                    } else {
                        const zipData = await zipResponse.json();
                        handleResponseData(zipData, assignmentId);
                    }
                } else {
                    window.location.href = `/assignments/edit/${assignmentId}/`;
                }
            } else {
                console.error('Error:', data.error);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    function handleResponseData(data, assignmentId) {
        if (data.message) {
            alert(data.message);
            modal.style.display = 'none';
            window.location.href = `/assignments/edit/${assignmentId}/`;  // Redirect to the edit assignment page
        } else if (data.error) {
            alert(data.error);
        }
    }

    function addAssignmentUnit() {
        const assignmentUnitIndex = document.querySelectorAll('.assignmentUnit').length;
        const assignmentUnit = document.createElement('div');
        assignmentUnit.classList.add('assignmentUnit');

        const nameInput = document.createElement('input');
        nameInput.setAttribute('type', 'text');
        nameInput.setAttribute('name', `units-${assignmentUnitIndex}-name`);
        nameInput.setAttribute('placeholder', 'File Name');
        assignmentUnit.appendChild(nameInput);

        const fileInput = document.createElement('input');
        fileInput.setAttribute('type', 'file');
        fileInput.setAttribute('name', `units-${assignmentUnitIndex}-file`);
        assignmentUnit.appendChild(fileInput);

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

});
