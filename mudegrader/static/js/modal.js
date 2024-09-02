document.addEventListener("DOMContentLoaded", function() {
    let modal = document.getElementById('importModal');
    let closeButton = document.querySelector('.close');
    let importBtn = document.querySelector('.data');
    let dropZone = document.getElementById('drop_zone');
    let fileInput = document.getElementById('fileInput');
    let uploadButton = document.getElementById('uploadButton');
    let formData = new FormData();

    // pop-up not shown on page load
    modal.style.display = 'none';

    // Open the modal when the import button is clicked
    importBtn.addEventListener('click', function() {
        modal.style.display = 'block';
    });

    // Close the modal when the close button (x) is clicked
    closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    // Optional: Close the modal when clicking outside the modal content
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    // Prevent default drag behaviors
    dropZone.addEventListener('dragover', function(event) {
        event.preventDefault();
        dropZone.style.backgroundColor = '#f0f0f0'; // Optional: change color on drag over
    });

    // Handle file drop
    dropZone.addEventListener('drop', function(event) {
        event.preventDefault();
        dropZone.style.backgroundColor = ''; // Optional: reset background color
        fileChangeHandler(event.dataTransfer.files);
    });

    // Handle file selection via file input
    fileInput.addEventListener('change', function() {
        fileChangeHandler(this.files);
    });

    // Upload files when the upload button is clicked
    uploadButton.addEventListener('click', function() {
        uploadFiles();
    });

    // Function to handle file changes
    function fileChangeHandler(files) {
        // Display file names in the drop zone
        let fileListDisplay = document.getElementById('fileList');

        for (let i = 0; i < files.length; i++) {
            // Store files in a FormData object for upload
            formData.append('file', files[i]);

            // Create a list item for each file and append to fileListDisplay
            let fileEntry = document.createElement('div');
            fileEntry.textContent = files[i].name; // Display file name
            fileEntry.style.color = '#4CAF50'
            fileListDisplay.appendChild(fileEntry);
        }

    }

    // Function to upload files
    function uploadFiles() {
        // we retrieve this from the place we hid it in the document
        // TODO: see if there is a better way
        let csrftoken = document.getElementById('csrfToken').value;

        // TODO: explain importURL
        fetch(importUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData,
            credentials: 'include'
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url; // This handles the redirect
            } else {
                return response.text(); // or response.json() if you expect JSON
            }
        }).then(data => {
                // alert('Files uploaded successfully.');
                modal.style.display = 'none'; // Close the modal upon successful upload
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }



});
