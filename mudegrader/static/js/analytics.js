// Display a message in the console to confirm JavaScript is successfully loaded and running
console.log('JavaScript is loaded and working!');

// Function to handle tab switching
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    
    // Get all elements with class="tab-content" and hide them
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab and add an "active" class to the button that opened the tab
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

// Function to initialize a chart
function initializeChart(ctx, labels, data, label) {
    return new Chart(ctx, {
        type: 'bar', // Specify the type of chart (bar chart)
        data: {
            labels: labels, // Labels for the x-axis
            datasets: [{
                label: label, // Label for the dataset
                data: data, // Data for the dataset
                backgroundColor: 'rgba(75, 192, 192, 0.2)', // Background color for bars
                borderColor: 'rgba(75, 192, 192, 1)', // Border color for bars
                borderWidth: 1 // Width of the bar borders
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true // Start y-axis at zero
                }
            }
        }
    });
}

// Function to update an existing chart with new data
function updateChart(chart, labels, data, label) {
    if (chart) {
        chart.data.labels = labels; // Update labels on x-axis
        chart.data.datasets[0].data = data; // Update dataset with new data
        chart.data.datasets[0].label = label; // Update label for the dataset
        chart.update(); // Refresh the chart to reflect changes
    }
}

// Execute this function when the window finishes loading
window.onload = function() {
    console.log('Window loaded and script running!');

    // Initialize various charts with initial data

    // Assignment grades chart
    var assignmentCtx = document.getElementById('assignmentChart').getContext('2d');
    var assignmentChart = initializeChart(assignmentCtx, assignmentLabels, assignmentData, 'Grades');

    // Exam grades chart
    var examCtx = document.getElementById('examChart').getContext('2d');
    var examChart = initializeChart(examCtx, examLabels, examData, 'Grades');

    // Pass rate chart
    var passRateCtx = document.getElementById('passRateChart').getContext('2d');
    var passRateChart = initializeChart(passRateCtx, passRateLabels, passRateData, 'Pass Rate');

    // Average grade chart
    var averageGradeCtx = document.getElementById('averageGradeChart').getContext('2d');
    var averageGradeChart = initializeChart(averageGradeCtx, averageGradeLabels, averageGradeData, 'Average Grade');

    // Grading progress chart
    var gradingProgressCtx = document.getElementById('submissionProgressChart').getContext('2d');
    var gradingProgressChart = initializeChart(gradingProgressCtx, submissionProgressLabels, submissionProgressData, 'Grading Progress');

    // Nationality rate chart
    var nationalityRateCtx = document.getElementById('nationalityRateChart').getContext('2d');
    var nationalityRateChart = initializeChart(nationalityRateCtx, nationalityRateLabels, nationalityRateData, 'Nationality Rate');

    // Participation rate chart
    var participationRateCtx = document.getElementById('participationRateChart').getContext('2d');
    var participationRateChart = initializeChart(participationRateCtx, participationRateLabels, participationRateData, 'Number of Participants');

    // Group performance chart
    var groupPerformanceCtx = document.getElementById('groupPerformanceChart').getContext('2d');
    var groupPerformanceChart = initializeChart(groupPerformanceCtx, groupPerformanceLabels, groupPerformanceData, 'Group Performance');

    // Event listener for the assignment dropdown change
    document.getElementById('assignmentDropdown').addEventListener('change', function() {
        var selectedAssignment = this.value;
        // Fetch new data for the selected assignment (example data shown here)
        var newLabels = ['A', 'B', 'C'];
        var newData = [10, 20, 30];
        // Update the assignment chart with new data
        updateChart(assignmentChart, newLabels, newData, `Grades for ${selectedAssignment}`);
        document.getElementById('selected-assignment').textContent = selectedAssignment;
    });

    // Event listener for the exam dropdown change
    document.getElementById('examDropdown').addEventListener('change', function() {
        var selectedExam = this.value;
        // Fetch new data for the selected exam (example data shown here)
        var newLabels = ['A', 'B', 'C'];
        var newData = [15, 25, 35];
        // Update the exam chart with new data
        updateChart(examChart, newLabels, newData, `Grades for ${selectedExam}`);
        document.getElementById('selected-exam').textContent = selectedExam;
    });

    // Event listener for the group dropdown change
    document.getElementById('groupDropdown').addEventListener('change', function() {
        var selectedGroup = this.value;
        if (selectedGroup) {
            // Fetch new data for the selected group
            var newLabels = Object.keys(groupGrades[selectedGroup]);
            var newData = Object.values(groupGrades[selectedGroup]);
            // Update the group grades table with new data
            updateGroupGradesTable(selectedGroup, newLabels, newData);
            document.getElementById('selected-group').textContent = selectedGroup;
        } else {
            // Clear the group grades table if no group is selected
            clearGroupGradesTable();
            document.getElementById('selected-group').textContent = 'Select a Group';
        }
    });
};

// Function to update the group grades table with new data
function updateGroupGradesTable(group, assignments, grades) {
    var tableBody = document.getElementById('groupGradesTable').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = ''; // Clear any existing rows in the table

    // Populate the table with new rows for each assignment and grade
    for (var i = 0; i < assignments.length; i++) {
        var row = tableBody.insertRow();
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        cell1.innerHTML = assignments[i]; // Assignment name
        cell2.innerHTML = grades[i]; // Grade
    }
}

// Function to clear all rows in the group grades table
function clearGroupGradesTable() {
    var tableBody = document.getElementById('groupGradesTable').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = ''; // Remove all rows from the table
}
