## Pet Health and Breed Identification System

AI-enabled Django web platform for pet breed identification, preliminary health assessment, vaccination tracking, and analytics dashboards.

### 1. Features (High-Level)

- **AI Breed Identification**: Upload pet images (dogs, cats) and get predicted breed with confidence scores.
- **Health Assessment**: Basic rule-based checks on visible issues (skin, fur, eyes, obesity indicators).
- **Veterinary Advisory**: Vaccination schedules, diet suggestions, hygiene and grooming tips.
- **Medical Records**: Vaccination history, treatments, prescriptions, and reminders.
- **Analytics Dashboards**: Charts for breed distribution, disease occurrence, vaccination compliance, and age-wise trends.

### 2. Tech Stack

- **Backend**: Django (Python)
- **AI / ML**: Google AutoML / Vertex AI Vision (via `google-cloud-aiplatform`) – pluggable client
- **Database**: SQLite (default) – can be upgraded to MySQL/PostgreSQL
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Visualization**: NumPy, pandas, Matplotlib, Seaborn (optional)

### 3. Local Development Setup (Windows)

From the project root (`c:\work\Pet Health and Breed Identification System`):

1. **Create and activate virtual environment**

   ```powershell
   py -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

3. **Create Django project (only once, if not already created)**

   ```powershell
   django-admin startproject petcare .
   ```

4. **Run initial migrations**

   ```powershell
   python manage.py migrate
   ```

5. **Create superuser (admin)**

   ```powershell
   python manage.py createsuperuser
   ```

6. **Run development server**

   ```powershell
   python manage.py runserver
   ```

Then open `http://127.0.0.1:8000/` in your browser.

### 4. High-Level Architecture

- **Apps (planned)**:
  - `accounts`: user registration, login, profiles.
  - `pets`: pet profiles, images, breed predictions, health assessment.
  - `records`: vaccinations, treatments, prescriptions.
  - `analytics`: dashboards and charts.
  - `advisory`: rule-based veterinary guidance and schedules.

Each module is kept loosely coupled so the AutoML client, rules, and visualization can be improved independently.

### 5. Next Steps (Implementation Roadmap)

1. Initialize Django project and core apps.
2. Implement user management (registration, login, profile).
3. Model pets, health records, and vaccination data.
4. Implement image upload and AI prediction integration hooks.
5. Implement health assessment and advisory logic.
6. Build dashboards and visualization pages.
7. Polish UI with Bootstrap and add documentation.

