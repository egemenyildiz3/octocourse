document.addEventListener('DOMContentLoaded', function () {
    const addCheckButton = document.getElementById('addCheckButton');
    const extraChecksContainer = document.getElementById('extraChecksContainer');

    addCheckButton.addEventListener('click', function () {
        addCheck();
    });

    document.querySelectorAll('.remove-check').forEach(button => {
        button.addEventListener('click', function () {
            button.parentElement.remove();
        });
    });

    function addCheck() {
        const checkDiv = document.createElement('div');
        checkDiv.className = 'extra-check';
        checkDiv.innerHTML = `
            <select name="checkType[]" class="check-type">
                <option value="naming_convention">Naming Convention (Regex)</option>
                <option value="file_existence">File Existence</option>
                <option value="file_type">File Type</option>
                <option value="file_location">File Location</option>
            </select>
            <div class="check-inputs">
                <!-- Dynamic inputs will be inserted here -->
            </div>
            <button type="button" class="mude-button danger remove-check">Remove</button>
        `;
        extraChecksContainer.appendChild(checkDiv);

        const checkTypeSelect = checkDiv.querySelector('.check-type');
        const checkInputsDiv = checkDiv.querySelector('.check-inputs');

        checkTypeSelect.addEventListener('change', function () {
            updateCheckInputs(checkInputsDiv, checkTypeSelect.value);
        });

        checkDiv.querySelector('.remove-check').addEventListener('click', function () {
            checkDiv.remove();
        });

        updateCheckInputs(checkInputsDiv, checkTypeSelect.value); // Initialize the inputs
    }

    function updateCheckInputs(checkInputsDiv, checkType) {
        checkInputsDiv.innerHTML = '';
        if (checkType === 'naming_convention') {
            checkInputsDiv.innerHTML = `
                <input type="text" name="checkValue[]" placeholder="Regex Pattern" class="check-value">
                <input type="hidden" name="checkExtra[]" value="null">
            `;
        } else if (checkType === 'file_existence') {
            checkInputsDiv.innerHTML = `
                <input type="text" name="checkValue[]" placeholder="File Name" class="check-value">
                <input type="text" name="checkExtra[]" placeholder="File Type" class="check-extra">
            `;
        } else if (checkType === 'file_type') {
            checkInputsDiv.innerHTML = `
                <input type="text" name="checkValue[]" placeholder="File Name" class="check-value">
                <input type="text" name="checkExtra[]" placeholder="Expected File Type" class="check-extra">
            `;
        } else if (checkType === 'file_location') {
            checkInputsDiv.innerHTML = `
                <input type="text" name="checkValue[]" placeholder="File Name" class="check-value">
                <input type="text" name="checkExtra[]" placeholder="Relative Path" class="check-extra">
            `;
        }
    }
});
