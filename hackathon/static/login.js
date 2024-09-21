function validateForm() {
    // Get form elements
    const userID = document.getElementById('userID').value;
    const password = document.getElementById('password').value;
    const message = document.getElementById('message');

    // Clear previous messages
    message.innerHTML = "";

    // Validate User ID and Password
    if (!userID || !validateUserID(userID)) {
        message.innerHTML = '<p style="color:red;">Please enter a valid User ID (e.g., ab123).</p>';
        return;
    }

    if (!password || password.length < 6) {
        message.innerHTML = '<p style="color:red;">Password should be at least 6 characters long.</p>';
        return;
    }

    // If valid, show success message
    message.innerHTML = '<p style="color:green;">Login successful!</p>';
}

function validateUserID(userID) {
    // Regular expression for validating User ID (letters followed by digits)
    const re = /^[a-zA-Z]+\d+$/;
    return re.test(userID);
}

// Function to update bed count
function updateBedCount(bedElement) {
    const bedCountElement = bedElement.querySelector('.bed-count');
    let currentCount = parseInt(bedCountElement.textContent, 10);

    if (currentCount > 0) {
        bedCountElement.textContent = currentCount - 1;
    } else {
        alert("No rooms available! Click ok to enter the waitlist");
    }
}

// Event listener for all book buttons
document.querySelectorAll('.book-button').forEach(button => {
    button.addEventListener('click', function() {
        const bedElement = this.closest('.bed');
        updateBedCount(bedElement);
    });
});
// Function to alert that patient has been discharged
function dischargePatient() {
    const userID = document.getElementById('userID').value;

    if (userID) {
        alert(Patient with User ID: ${userID} has been successfully discharged.);
    } else {
        alert('Please enter a valid User ID.');
    }
}

// Add event listener to the Discharge button
document.querySelector('input[type="submit"]').addEventListener('click', (e) => {
    e.preventDefault(); // Prevents form submission
    dischargePatient();
})



