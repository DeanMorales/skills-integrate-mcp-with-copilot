# Mergington High School Activities API

A FastAPI application for viewing extracurricular activities. Anyone can view
the activities and rosters; only authenticated teachers can register or
unregister students.

## Features

- View all available extracurricular activities
- Teacher login for roster changes
- Sign up for and unregister students from activities as a teacher

## Getting Started

1. Install the dependencies from the repository root:

   ```
   pip install -r requirements.txt
   ```

2. From the repository root, create a teacher account. The password is
   prompted securely and stored as a salted hash in the local, git-ignored
   `src/teachers.json` file:

   ```
   python -m src.manage_teachers teacher-username
   ```

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

The tracked `teachers.example.json` shows the expected JSON structure. Do not
commit `teachers.json` or share teacher passwords. Basic credentials are sent
to the API for each roster change, so use HTTPS when deploying outside a local
development environment. Logging out clears the credentials held in browser
memory.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                     | Validate teacher credentials using HTTP Basic authentication       |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student signup                                         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only unregister                                         |

The browser login form remains available to teachers; the activity list and
participant rosters remain publicly viewable. The API independently enforces
authentication for both mutation endpoints.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity data is stored in memory and resets when the server restarts. Teacher
account hashes are stored separately in the local `teachers.json` file.
