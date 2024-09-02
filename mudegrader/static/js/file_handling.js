document.addEventListener('DOMContentLoaded', function () {
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

    attachIconEvents();
    addFileLinksEventListeners();
});
