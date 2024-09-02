
![Coverage Badge](https://gitlab.ewi.tudelft.nl/cse2000-software-project/2023-2024/cluster-b/02c/mude-grader/-/jobs/artifacts/dev/raw/coverage.svg?job=unittest)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-1.0.58-blue.svg)


# MUDE Grader

Welcome to the front page of (MUDE Grader)! The all in one solution for your course management needs.

<p align="center">
   <img src="/uploads/db3af60db70915d62fbea9e2a4c580f3/octo.png" style="display: block; margin: 0 auto;" alt="octo" width="300" height="300">
   <!-- ![octo](/uploads/db3af60db70915d62fbea9e2a4c580f3/octo.png) -->
</p>


### Available Features:

- Manage all your faculty courses with ease!
- See completion rates of assignments in real time!
- Give granular or general feedback to students.
- Upload ready-to-go assignments as a zip.
- Comprehensive assignment management.
- Student and group management.
- and much more...

### Experimental: 

- [X] Scheduling regular checks on student submissions
- [X] Apply various checks on student submissions
- [ ] 
- [ ]

### Features that would be really cool:

- Plagiarism/Fraud Detection
- LLM integration for teacher aided grading 
- Automatic test case generation
- 

### Dependencies and Assumptions

To use this application in the intended manner, there are some prerequisites that needs to be set in place. One of these is a Gitlab subgroup that this application will have access to. This is the main place the backend operates to/from. 

The minimum hardware specifications for this application has not been tested yet in detail. Although it must be noted that in a class with ~300 students and weekly assignments which are scheduled to be given daily feedback the load can go up pretty high per course. Hence it is asdvices to have minimum 4 cores available at any time.


The Project is developed by Jasper, Yusuf, Arslan, Egemen, Shomis. (description to be added)

## Table of Contents
- [Overview](#overview)
- [Applications](#applications)
  - [User Authentication](#user-authentication)
  - [Assignment Management](#assignment-management)
  - [Grading and Feedback](#grading-and-feedback)
  - [Analytics Dashboard](#analytics-dashboard)
  - [GitLab Manager](#gitlab-manager)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Structure](#structure)
- [URLs and API Endpoints](#urls-and-api-endpoints)
  - [Main URLs](#main-urls)
  - [Grader and Feedback Tool URLs](#grader-and-feedback-tool-urls)
  - [Assignment Manager URLs](#assignment-manager-urls)
  - [Analytics URLs](#analytics-urls)
- [Analytics Details](#analytics-details)
- [Environment Setup](#environment-setup)
- [Technologies Used](#technologies-used)
- [Celery](#celery)
- [Use Cases](#use-cases)
   - [Creating Assignments](#creating-assignments)
   - [Assignment Management](#assignment-management)
   - [Distributing Assignments](#distributing-assignments)
   - [Auto-grading Assignments](#auto-grading-assignments)
   - [Providing Feedback](#providing-feedback)
   - [Providing Analytics](#providing-analytics)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview
The MUDE Grader project is a comprehensive educational platform developed to enhance the management of assignments, grading, and feedback for the Master’s program in Civil Engineering and Geosciences at TU Delft. This project aims to streamline the workflow for course instructors by automating and organizing various processes, thereby reducing manual errors and saving time.

## Applications

### User Authentication
Handles user registration, login, password management, and user profile.

### Assignment Management
Manages courses, assignments, and related entities. Allows the creation, editing, and deletion of courses and assignments, as well as importing and exporting data.

### Grading and Feedback
Facilitates the grading of assignments and providing feedback to students. Includes features for viewing student submissions, sending feedback, and collecting submissions.

### Analytics Dashboard
Provides analytical insights and dashboards to monitor various metrics such as average grades, pass rates, and student performance.

### GitLab Manager
The GitLab Manager is responsible for interacting with GitLab to manage repositories, handle CRUD operations for students and groups, distribute files, collect submissions by cloning repositories, and send feedback by pushing to repositories. It does not provide APIs but instead offers functions that other applications within the project can use. The GitLab Manager does not handle merge requests or any other GitLab-specific workflows.


## Installation

### Prerequisites
- Docker


### Steps
1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo.git
    ```
2. Navigate to the project directory:
    ```bash
    cd your-repo
    ```
3. Build and start the Docker containers:
    ```bash
    docker-compose up --build
    ```

That's it! The application should now be running and accessible at `http://localhost`.

## Configuration
Ensure you configure your `settings.py` file with the correct database settings and other necessary configurations such as `MEDIA_ROOT`, `MEDIA_URL`, and `STATIC_URL`.


### Running the Application

To start the application, follow these steps:

1. **Docker Compose**: Use Docker Compose to build and run the application.

   ```bash
   docker-compose up --build
   ```

2. **Access the Application**: Once the containers are running, you can access the application in your web browser at `http://localhost`.

3. **Stop the Application**: To stop the application, run:

   ```bash
   docker-compose down
   ```

### Structure

The project is organized into several Django applications, each responsible for a specific part of the functionality:

1. **User Authentication**: Manages user registration, login, and authentication.
   - **URL Patterns**: `authentication/`
   - **Key Views**: `login_view`, `logout_view`, `register_view`

2. **Assignment Management**: Handles the creation, editing, and deletion of courses and assignments.
   - **URL Patterns**:
     - `courses/`
     - `courses/add/`
     - `courses/details/<int:pk>/`
     - `assignments/<int:course_id>/`
     - `assignments/add`
     - `assignments/details/<int:pk>/`

3. **Grading and Feedback**: Manages the grading of assignments and provides feedback to students.
   - **URL Patterns**:
     - `assignments/`



## URLs and API Endpoints

### Main URLs
These are the primary URLs for the application:

```
comments/delete/<int:comment_id>/
authentication/
admin/
grading/
analytics/
assignment_manager/
privacy_policy/
app/project_files/<path:.*>
```

### Grader and Feedback Tool URLs
These URLs are related to the grading and feedback functionalities:

```
assignments/
students_groups/<int:assignment_id>/
search/students/<int:assignment_id>/
filter/students/<int:assignment_id>/
search_group/<int:assignment_id>/
filter_group/<int:assignment_id>/
send_feedback/<int:assignment_id>/
submission_list/<int:assignment_id>/<int:stu_id>/
submission/<int:submission_id>/
submission_unit/<int:unit_id>/
student/<int:student_id>/submissions/
group/<int:group_id>/submissions/
collect_submissions/<int:assignment_id>/
```

### Assignment Manager URLs
These URLs manage courses, assignments, and related entities:

```
courses/
courses/add/
courses/details/<int:pk>/
courses/delete/<int:course_id>/
courses/edit/<int:pk>/
courses/staff/<int:course_id>/
courses/export/
courses/import/
courses/edit-tags/<int:course_id>/
courses/<int:course_id>/delete-tag/<int:tag_id>/

assignments/<int:course_id>/
assignments/add
assignments/details/<int:pk>/
assignments/delete/<int:assignment_id>/
assignments/edit/<int:pk>/
assignments/publish/<int:assignment_id>/
assignments/export/
assignments/publish_manually/<int:assignment_id>/
assignments/publish_manually_individual/<int:assignment_id>/<int:student_id>/
assignments/publish_manually_group/<int:assignment_id>/<int:group_id>/
assignments/import/
assignments/import_zip/<int:assignment_id>/
assignments/download/<int:assignment_id>/

assignments/units/delete/<int:unit_id>/

students/
students/add
students/details/<int:pk>/
students/delete/<int:student_id>/
students/edit/<int:student_id>/
students/filter/
students/search/
students/export/
students/import/
students/exams/<int:student_id>
students/timeline/<int:student_id>/

groups/
groups/add
groups/details/<int:pk>/
groups/delete/<int:group_id>/
groups/edit/<int:group_id>/
groups/filter/
groups/search/
groups/add-student/
groups/remove-student/
groups/search-student/
groups/timeline/<int:group_id>/
```

### Analytics URLs
These URLs provide access to the analytics dashboard:

```
analytics/
```

## Analytics Details
The analytics section provides detailed insights and metrics, including:
- Average grades
- Exam grades
- Time left
- Pass rate
- Grading progress
- Nationality rates
- Exam participants
- Group performance
- Group grades
- Student performance
- Assignment overview

## Environment Setup

### Docker (Required)
To run this project, you need to have Docker installed on your system. Follow these steps:

1. Install Docker on your system.

### Docker Usage
You can use Docker Compose to build and run the project. Follow these steps:

1. Navigate to the project directory containing the `docker-compose.yml` file.
2. Build the Docker images:
   ```
   docker-compose build
   ```
   This command builds the Docker images defined in the `docker-compose.yml` file.
3. Start the containers:
   ```
   docker-compose up
   ```
   This command starts the containers defined in the `docker-compose.yml` file.
4. Access the application in your web browser at `http://localhost`.

### Terminal
To open a container in a terminal:
1. Type the following command. You must already have Docker installed.
   ```
   docker exec -it <your_container_id> bash
   ```

## Tests
To run the tests:
1. Navigate into the project folder in the Docker container.
2. Navigate to `mude-grader/mudegrader`.
3. Run the following command:
   ```
   python manage.py test
   ```
   This will run the tests in the project.

## Database Reset
To clean and remove everything from the database, run the following command:
   ```
   python /app/mudegrader/manage.py flush
   ```

## Superuser
To create a superuser and manage objects manually:
   ```
   python manage.py createsuperuser
   ```

## Migrations
After changing Django models in any application, tables in the current database need to be changed as well. One safer way of doing this is to back up or export all data and remake the database. Deleting the migrations in the application and letting it remake them creates the new tables.

For Unix-like operating systems (Linux, macOS):
   ```
   find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
   ```
## Celery

By default this application runs its background tasks on a single celery worker (which communicates with the application through Redis as a broker). Depending on the use case and scale it is deployed, the need for workers will increase hence celery needs to be configured to accomodate the workload of the application.



## Use Cases

### Creating Assignments
**Description**: Instructors can create assignments by specifying metadata such as title, description, due date, and the total points. They can add relevant assignment units and instructions.

**Steps**:
1. Navigate to the Assignment Management section.
2. Click on "Create New Assignment."
3. Fill in the assignment details including title, description, and due date.
4. Add assignment units (files) by uploading them or creating them directly in the system.
5. Specify public and private tests for auto-grading.
6. Save and review the assignment structure.
7. Optionally, add comments for other instructors.

**Outcome**: A new assignment is created and saved in the system, ready to be distributed to students.

### Assignment Management
**Description**: Instructors manage courses, assignments, and related entities. This includes creating, editing, viewing, and deleting assignments, as well as importing and exporting data.

**Steps**:
1. Navigate to the Assignment Management section.
2. View the list of existing assignments.
3. Select an assignment to view details, edit, or delete.
4. Use the import/export feature to manage assignments in bulk.

**Outcome**: Assignments are efficiently managed within the system, ensuring that all necessary data is up-to-date and accurate.

### Distributing Assignments
**Description**: Assignments can be distributed to students or groups on their respective GitLab repositories. Instructors can choose to publish assignments immediately or schedule them for later.

**Steps**:
1. Navigate to the Assignment Management section.
2. Select the assignment to be distributed.
3. Choose the target student or group repositories.
4. Click "Distribute" to publish the assignment.

**Outcome**: Assignments are published to the selected repositories, making them accessible to students for submission.

### Auto-grading Assignments
**Description**: The system can run predefined public and private tests on student submissions to automate grading. Public tests are available to students for local checks, while private tests are run on the server.

**Steps**:
1. During assignment creation, define public and private tests.
2. Students run public tests locally.
3. The system runs private tests on the server at specified intervals.
4. Auto-grading results are stored and made available to instructors.

**Outcome**: Student submissions are automatically graded based on predefined tests, reducing the grading workload for instructors.

### Providing Feedback
**Description**: Instructors provide feedback on student submissions through an intuitive interface. Feedback can be given at the task level, submission unit level, or overall submission level.

**Steps**:
1. Navigate to the Grading and Feedback section.
2. Select a student submission.
3. Review the submission and provide feedback using the interface.
4. Save and submit the feedback.

**Outcome**: Students receive detailed and timely feedback on their assignments, helping them improve their performance.

### Providing Analytics
**Description**: The system provides analytical insights into student performance, including average grades, pass rates, and submission timelines. Instructors can use these insights to monitor and improve course performance.

**Steps**:
1. Navigate to the Analytics Dashboard.
2. Select the desired metrics and parameters.
3. View detailed analytics reports and charts.

**Outcome**: Instructors gain valuable insights into student performance and course effectiveness, enabling data-driven decision-making.

## Documentation

This project provides in-built documentation to aid usage and further development. This projects incorporates [Sphinx-Doc](https://www.sphinx-doc.org/en/master/) for its documentation and serves it with the [RTD](https://docs.readthedocs.io/en/stable/) flavour.

The documentation can be accessed [here](https://mude-utilities.citg.tudelft.nl/docs/build/html/index.html) and to generate further documentation in case of the development being picked up, you can execute:

```
make (pdf | html | latexpdf)
```
or any of the options you'd like from the 
```/mudegrader/docs/``` directory level. Any further configuration of this generator can alseo be done through ```/mudegrader/docs/source/conf.py```.

## Technologies Used
- Django
- Django REST Framework
- Docker
- GitLab
- Celery
- Redis
- PostgreSQL

## Contributing
If you would like to contribute to this project, please follow the standard GitHub workflow: fork the repository, make your changes, and submit a pull request.

## License
This project is licensed under [WTFPL](http://www.wtfpl.net/). Usage outside these terms will lead to legal actions. 

## Contact
For any inquiries or questions, please do not contact us 


_The Project is developed by Jasper, Yusuf, Arslan, Egemen, Shomis. (description to be added)_
