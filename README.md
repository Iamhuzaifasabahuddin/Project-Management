# Project Management System

A robust, feature-rich Project Management System built with Django, designed to streamline workspaces, client management, team collaboration, and task tracking.

## 🚀 Features

- **Workspace Management:** Organize projects into hierarchical workspaces.
- **Client & Payment Tracking:** Manage clients, track payments (Card, Wire Transfer, Cheque), and monitor outstanding balances.
- **Team Collaboration:** Create teams with specific roles (Developer, Designer, Marketing, etc.) and assign team leads.
- **Task Management:** Create, assign, and track tasks with status updates (Pending, Awaiting Approval, Completed) and due date notifications.
- **Interactive Posts:** Communication hub for tasks with support for file attachments and comments.
- **User Authentication:** Secure login, registration with email verification, and social auth (Google, GitHub) via `django-allauth`.
- **Asynchronous Workflows:** Background processing for emails and Slack notifications using Celery and Redis.
- **Cloud Storage:** Integrated with AWS S3 compatible storage (T3 Storage API) for media files.

## 🛠 Tech Stack

- **Backend:** Python 3.x, Django 4.2.30
- **Database:** PostgreSQL / MySQL (configured via DATABASE_URL)
- **Task Queue:** Celery with Redis broker
- **Storage:**
  - **Static Files:** WhiteNoise
  - **Media Files:** django-storages (S3 compatible)
- **Frontend:** Bootstrap 5, Select2, Vanilla JavaScript
- **Deployment:** Ready for platforms like Railway/Heroku (Procfile included)

## 📁 Project Structure

```text
ProjectManagement/
├── ProjectManagement/      # Core settings and configuration
├── accounts/               # User authentication, profiles, and registration
├── Posts/                  # Tasks, posts, comments, and file uploads
├── Teams/                  # Team and role management
├── workspaces/             # Workspace and client management
├── Project_Static_Files/   # Global static assets (CSS, JS)
├── templates/              # Global HTML templates
├── manage.py               # Django management script
└── requirements.txt        # Project dependencies
```

## ⚙️ Setup and Installation

### Prerequisites

- Python 3.13+
- Redis (for Celery and Caching)
- A relational database (PostgreSQL/MySQL)
- AWS S3 compatible storage (for media files)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Project-Management
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r ProjectManagement/requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in `ProjectManagement/` (refer to `settings.py` for required keys):
   ```env
   DEBUG=False
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:password@localhost:5432/dbname
   REDIS_URL=your-redis-url
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ALLOWED_HOSTS=localhost, your-railway-app-url / domain
   CSRF_TRUSTED_ORIGINS=http://localhost:8000, https://your-railway-app-url / domain
   PORT="8000"
   ```

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

### 🐝 Celery Worker

To handle background tasks (emails, notifications), start the Celery worker:

```bash
celery -A ProjectManagement worker --loglevel=info
```

For email and slack specific queues:
```bash
celery -A ProjectManagement worker --pool=threads --concurrency=4 -l info -Q celery,email,slack
```

## 🚢 Deployment

The project includes a `Procfile` and is optimized for deployment on platforms like Railway. Ensure all environment variables are properly set in your production environment.

## 📄 License

[Insert License Type Here, e.g., MIT]
