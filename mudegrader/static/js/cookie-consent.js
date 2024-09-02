/**
 * Initializes the cookie consent banner functionality when the DOM content is fully loaded.
 * 
 * This script checks if the user has already accepted the cookie consent. If not, it displays
 * the cookie consent banner. When the user clicks the "Accept" button, it sets a cookie to
 * remember the user's consent and hides the banner.
 */
document.addEventListener('DOMContentLoaded', function () {
    /**
     * Checks if the cookie consent has been given. If not, displays the cookie consent banner.
     */
    if (!document.cookie.split('; ').find(row => row.startsWith('cookie_consent='))) {
        document.getElementById('cookie-consent-banner').style.display = 'block';
    }

    /**
     * Adds an event listener to the "Accept" button to set the cookie consent and hide the banner.
     */
    document.getElementById('accept-cookies').addEventListener('click', function () {
        // Set the cookie consent with a max-age of one year
        document.cookie = "cookie_consent=accepted; path=/; max-age=" + 60 * 60 * 24 * 365;
        // Hide the cookie consent banner
        document.getElementById('cookie-consent-banner').style.display = 'none';
    });
});
