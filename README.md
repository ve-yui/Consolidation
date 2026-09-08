# News Application - Django Capstone

A Django news application implementing the HyperionDev Capstone requirements.

## Features

- Custom user model with Reader, Editor and Journalist roles.
- Journalists create articles; a publisher is optional.
- Publishers can have multiple assigned editors and journalists.
- Editor article approval workflow with subscriber email notification.
- Approved articles are posted to the internal approved-article API.
- Reader subscriptions to publishers and journalists.
- Newsletter creation and article curation.
- Django REST Framework API with JWT authentication.
- Role-based Django groups and permissions.
- MariaDB configuration through environment variables.
- Docker and Docker Compose support.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`. The application loads `.env` locally even when Docker is not used.
4. Run migrations:
   `python manage.py migrate`
5. Optional but recommended for evaluation: create demo accounts and role groups:
   `python manage.py setup_demo_data`
6. Create an administrator if needed:
   `python manage.py createsuperuser`
7. Start the server:
   `python manage.py runserver`

The development email backend prints email messages to the terminal.

## Demo credentials for evaluation

The setup command creates these accounts (development/evaluation use only):

| Role | Username | Password |
| --- | --- | --- |
| Editor | `demo_editor` | `EditorPass123!` |
| Journalist | `demo_journalist` | `JournalistPass123!` |
| Reader | `demo_reader` | `ReaderPass123!` |

Public registration intentionally allows only Reader and Journalist accounts. Editors are created through the setup command or Django admin so that editor privileges cannot be self-assigned through public registration.

## Publisher management workflow

1. Log in as `demo_editor` (or an editor created in the admin).
2. Select **Manage Publishers** in the navigation.
3. Choose **Create Publisher**.
4. Enter the publisher name and description.
5. Select one or more existing Editor and Journalist accounts for that publisher.
6. Save the publisher.
7. Use **Edit** on the publisher to change its assigned staff, or **Delete** to remove it.

The same publisher assignments are available through Django admin under **Publishers**.

## Article workflow

A journalist is always the author of an article. The journalist may leave the publisher blank for an independent article or select a publisher they are associated with. After creation, the article remains pending until an editor approves it.

## Approval workflow

1. A journalist creates an article.
2. An editor reviews the pending article.
3. The editor approves it.
4. Readers subscribed to the article's journalist or publisher receive an email.
5. The application POSTs the approved article to `/api/approved/` using the internal API key.

## API

JWT:
- `POST /api/token/`
- `POST /api/token/refresh/`

Articles:
- `GET /api/articles/`
- `GET /api/articles/subscribed/`
- `GET /api/articles/<id>/`
- `POST /api/articles/`
- `PUT /api/articles/<id>/`
- `DELETE /api/articles/<id>/`

Additional endpoints expose users, publishers, newsletters, and the internal approved-article log.

## Testing

Run:

`python manage.py test`

The test suite covers authentication, subscriptions, article creation/update/delete permissions, publisher articles, newsletters, and the approval notification/API workflow.

## MariaDB

The project uses MariaDB when `DB_NAME` is supplied. SQLite is used as a convenient local fallback when no database environment variables are set.

## Docker

This project includes a `docker-compose.yml` file that starts both the Django web service and the MariaDB database.

Build the images and start the full environment:

```bash
docker compose up --build
```

Then open the application at `http://localhost:8000`.

To stop the services, press `Ctrl+C` and run:

```bash
docker compose down
```
