# Collaborative Event Management System

A RESTful API for a collaborative event scheduling application built with **FastAPI** and **PostgreSQL**.

## 🚀 Features

- **User Authentication**: Secure login and registration using JWT
- **Event Management**: Full CRUD on events
- **Collaborative Editing**: Share events with other users with defined permission levels
- **Version Control**: History tracking and version restoration
- **Conflict Resolution**: Handles concurrent edits
- **Recurring Events**: Schedule repeating events

## 🛠 Tech Stack

| Layer         | Technology            |
|--------------|------------------------|
| Backend       | FastAPI (Python 3.10+) |
| ORM           | SQLAlchemy             |
| Database      | PostgreSQL             |
| Auth          | JWT Tokens             |
| Validation    | Pydantic               |
| Deployment    | Render                 |

---

## 🔐 Authentication Flow

1. User **registers** with `username`, `email`, `password`
2. User **logs in**, receives **JWT token**
3. Token is used in the `Authorization` header (`Bearer <token>`)
4. Token expires after 30 minutes (configurable)
5. Token can be **refreshed**

### Endpoints

- `POST /api/auth/register` → Register
- `POST /api/auth/login` → Get token
- `POST /api/auth/refresh` → Refresh token
- `POST /api/auth/logout` → Client-side only

---

## 👥 Permission Levels

| Role    | Capabilities                                  |
|---------|-----------------------------------------------|
| Owner   | Full control, manage permissions, delete      |
| Editor  | Edit and view event                           |
| Viewer  | Read-only                                     |

---

## 📦 Data Models

### User

| Field           | Type        |
|----------------|-------------|
| id             | Integer (PK)|
| username       | String (Unique) |
| email          | String (Unique) |
| hashed_password| String      |
| is_active      | Boolean     |
| created_at     | DateTime    |
| updated_at     | DateTime    |

---

### Event

| Field             | Type              |
|------------------|-------------------|
| id               | Integer (PK)      |
| title            | String            |
| description      | Text              |
| start_time       | DateTime          |
| end_time         | DateTime          |
| location         | String            |
| is_recurring     | Boolean           |
| recurrence_pattern | JSONB           |
| owner_id         | Integer (FK)      |
| created_at       | DateTime          |
| updated_at       | DateTime          |

---

### Permission

| Field       | Type         |
|------------|--------------|
| id         | Integer (PK) |
| event_id   | Integer (FK) |
| user_id    | Integer (FK) |
| role       | String       |
| created_at | DateTime     |
| updated_at | DateTime     |

---

### EventVersion

| Field             | Type         |
|------------------|--------------|
| id               | Integer (PK) |
| event_id         | Integer (FK) |
| data             | JSONB        |
| created_by       | Integer (FK) |
| created_at       | DateTime     |
| change_description | Text       |

---

## 🌐 API Endpoints

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

### Events

- `GET /api/events` — Get all user events  
- `POST /api/events` — Create event  
- `GET /api/events/{event_id}` — Get event  
- `PUT /api/events/{event_id}` — Update event  
- `DELETE /api/events/{event_id}` — Delete event  
- `POST /api/events/batch` — Create multiple events  

### Collaboration

- `POST /api/events/{event_id}/share` — Share event with another user  
- `GET /api/events/{event_id}/permissions` — List permissions  
- `PUT /api/events/{event_id}/permissions/{permission_id}` — Update permission  
- `DELETE /api/events/{event_id}/permissions/{permission_id}` — Remove permission  

### Version Control

- `GET /api/events/{event_id}/history` — Full version history  
- `GET /api/events/{event_id}/history/{version_id}` — Get specific version  
- `POST /api/events/{event_id}/revert/{version_id}` — Revert to previous version  
- `GET /api/events/{event_id}/diff` — Compare versions  

---

## 🧪 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Git

### Local Setup

```bash
git clone https://github.com/yourusername/event-management-system.git
cd event-management-system

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### .env Example

```env
SECRET_KEY=your_secure_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://username:password@localhost:5432/event_management
```

### Create Database

```sql
CREATE DATABASE event_management;
```

### Run App

```bash
python run.py
```

Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 Project Structure

```
event-management-system/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   └── utils/
├── tests/
├── .env
├── requirements.txt
└── run.py
```

---

## 🚀 Deployment (Render)

1. Push to GitHub
2. Create a new Web Service on [Render](https://render.com/)
3. Connect to GitHub
4. Set Environment Variables
5. Deploy!

---

**Maintainer**: `yourusername`
