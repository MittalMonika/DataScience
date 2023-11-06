// This function will run once the page is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Getting the link element by its ID
    var mySpecialLink = document.getElementById('mySpecialLink');

    // If the element exists, we proceed
    if (mySpecialLink) {
        // Adding a click event listener to the link
        mySpecialLink.addEventListener('click', function(event) {
            // Preventing the default behavior of the link click
            event.preventDefault();

            // Opening two URLs in new tabs
            window.open('PredictPrice_JP.html');
            window.open('YourSecondPage.html'); // Replace with your second URL
        });
    } else {
        // If the element doesn't exist, it will be logged in the console
        console.error('Link not found!');
    }
});

