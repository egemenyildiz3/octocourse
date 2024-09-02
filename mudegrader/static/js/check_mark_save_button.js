document.addEventListener('DOMContentLoaded', function() {
    let checkMark = document.getElementById('check-mark');
    let saveText = document.getElementById('save-text');

    const urlParams = new URLSearchParams(window.location.search);
    const saved = urlParams.get('saved');
    if (saved) {
        checkMark.classList.remove('hide');
        checkMark.classList.add('show');

        saveText.classList.add('hide')
        saveText.classList.remove('show-instant')

        setTimeout(function() {
            checkMark.classList.remove('show');
            checkMark.classList.add('hide');

            saveText.classList.add('show-instant')
            saveText.classList.remove('hide')
        }, 2000 );
    }
});