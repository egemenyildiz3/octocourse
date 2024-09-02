Welcome to MUDE Grader's documentation!
=======================================

This documentation provides a comprehensive guide to using the MUDE Grader. 
Here you will find information on various modules and functionalities 
that are part of the MUDE Grader toolset. 

Please use the navigation below to access detailed documentation for each module.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   gitlabmanager
   assignment_manager
   graderandfeedbacktool
   
   analytics
   authentication
   services

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Available Features
==================

- Manage all your faculty courses with ease!
- See completion rates of assignments in real time!
- Give granular or general feedback to students.
- Upload ready-to-go assignments as a zip.
- Comprehensive assignment management.
- Student and group management.
- and much more...

Experimental
============

- [X] Scheduling regular checks on student submissions
- [X] Apply various checks on student submissions
- [ ] 
- [ ]

Features that would be really cool
===================================

- Plagiarism/Fraud Detection
- LLM integration for teacher aided grading
- Automatic test case generation
- 

Dependencies and Assumptions
============================

To use this application in the intended manner, there are some prerequisites that need to be set in place. One of these is a GitLab subgroup that this application will have access to. This is the main place the backend operates to/from.

The minimum hardware specifications for this application have not been tested yet in detail. Although it must be noted that in a class with ~300 students and weekly assignments which are scheduled to be given daily feedback, the load can go up pretty high per course. Hence it is advised to have a minimum of 4 cores available at any time.

The Project is developed by Jasper, Yusuf, Arslan, Egemen, Shomis. (description to be added)


Overview
========

The MUDE Grader project is a comprehensive educational platform developed to enhance the management of assignments, grading, and feedback for the Master’s program in Civil Engineering and Geosciences at TU Delft. This project aims to streamline the workflow for course instructors by automating and organizing various processes, thereby reducing manual errors and saving time.

Applications
============

User Authentication
-------------------

Handles user registration, login, password management, and user profile.

Assignment Management
----------------------

Manages courses, assignments, and related entities. Allows the creation, editing, and deletion of courses and assignments, as well as importing and exporting data.

Grading and Feedback
--------------------

Facilitates the grading of assignments and providing feedback to students. Includes features for viewing student submissions, sending feedback, and collecting submissions.

Analytics Dashboard
-------------------

Provides analytical insights and dashboards to monitor various metrics such as average grades, pass rates, and student performance.

GitLab Manager
--------------

The GitLab Manager is responsible for interacting with GitLab to manage repositories, handle CRUD operations for students and groups, distribute files, collect submissions by cloning repositories, and send feedback by pushing to repositories. It does not provide APIs but instead offers functions that other applications within the project can use. The GitLab Manager does not handle merge requests or any other GitLab-specific workflows.

Installation
============

Prerequisites
-------------

- Docker

Steps
-----

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

Configuration
=============

Ensure you configure your `settings.py` file with the correct database settings and other necessary configurations such as `MEDIA_ROOT`, `MEDIA_URL`, and `STATIC_URL`.

Running the Application
=======================

To start the application, follow these steps:

1. **Docker Compose**: Use Docker Compose to build and run the application.

   ```docker-compose up --build```

2. **Access the Application**: Once the containers are running, you can access the application in your web browser at `http://localhost`.

3. **Stop the Application**: To stop the application, run:

   ```bash
   docker-compose down
   ```

Structure
----------

The project is organized into several Django applications, each responsible for a specific part of the functionality:

1. **User Authentication**: Manages user registration, login, and authentication.
   - **URL Patterns**: `authentication/`
   - **Key Views**: `login_view`, `logout_view`, `register_view`

2. **Assignment Management**: Handles the creation, editing, and deletion of courses and assignments.
   **URL Patterns**:
   - `courses/`
   - `courses/add/`
   - `courses/details/<int:pk>/`
   - `assignments/<int:course_id>/`
   - `assignments/add`
   - `assignments/details/<int:pk>/`

3. **Grading and Feedback**: Manages the grading of assignments and provides feedback to students.
   - **URL Patterns**:
   - `assignments/`


2. **Access the Application**: Once the containers are running, you can access the application in your web browser at `http://localhost`.

3. **Stop the Application**: To stop the application, run:

   ```bash
   docker-compose down
   ```

Documentation
-------------
This project provides in-built documentation to aid usage and further development. This projects incorporates [Sphinx-Doc](https://www.sphinx-doc.org/en/master/) for its documentation and serves it with the [RTD](https://docs.readthedocs.io/en/stable/) flavour.

The documentation can be accessed [here](broken link) and to generate further documentation in case of the development being picked up, you can execute:

```
make (pdf | html | latexpdf)
```
or any of the options you'd like from the 
```/mudegrader/docs/``` directory level. Any further configuration of this generator can alseo be done through ```/mudegrader/docs/source/conf.py```.

Technologies Used
-----------------
- Django
- Django REST Framework
- Docker
- GitLab
- Celery
- Redis
- PostgreSQL

Contributing
-------------
If you would like to contribute to this project, please follow the standard GitHub workflow: fork the repository, make your changes, and submit a pull request.

License
------------
This project is licensed under [WTFPL](http://www.wtfpl.net/). Usage outside these terms will lead to legal actions. 


_The Project is developed by Jasper, Yusuf, Arslan, Egemen, Shomis. (description to be added)_

