# Find-Job-App

A full-stack job marketplace platform with real-time messaging and application management. Built with Flask, SQLAlchemy, WebSockets, and Docker.

Live Demo: [https://your-railway-url.railway.app](https://your-railway-url.railway.app)

## Overview

Find-Job-App serves two user types: Job Seekers and Companies. The platform facilitates job discovery, applications, and direct communication between candidates and recruiters.

## Core Features

**Job Management**
- Browse and filter job listings by title, location, and salary
- Companies post and manage job listings
- Toggle job active/inactive status

**Job Applications**
- Job seekers apply to positions with resume uploads
- Companies review applications and download resumes
- Application status tracking (pending, accepted, rejected, under_review)
- Real-time notifications on status changes

**Direct Messaging**
- Create chat rooms between users
- Real-time WebSocket-based messaging
- User search for initiating conversations

**User Profiles**
- Job seekers showcase professional experience and skills
- Companies display company information and social links
- View other users' profiles

**Notifications**
- Real-time alerts via WebSocket (Socket.IO)
- Mark notifications as read/delete
- Application status updates and job application alerts

## Technology Stack

Backend: Flask, Flask-SQLAlchemy, Flask-SocketIO
Database: MySQL 8.0, Redis 7
Server: Gunicorn with Eventlet
Frontend: Jinja2, Bootstrap 5, JavaScript
Deployment: Docker, Railway

## Quick Start (Local)

```bash
# Clone repository
git clone ...
cd find-job-app

# Copy environment template
cp .env.example .env

# Start with Docker Compose
docker-compose up

# Or with Makefile commands
make build

# Access at http://localhost:5001
```

To stop: `docker-compose down` or `make down`

## Architecture

- **User Model**: Polymorphic inheritance (User -> Person/Company)
- **Database**: Connection pooling, auto table creation with retry logic
- **Real-time**: Redis message queue for WebSocket scalability
- **Rate Limiting**: Redis-backed rate limiter (development uses in-memory)
- **Security**: Role-based access control, password hashing, secure file handling

## API Endpoints

**Jobs**: POST/GET /job/create, /job/info, /job/update, /job/apply, /job/deactivate
**Applications**: GET/POST /application/list, /application/detail, /application/download_resume, /application/update_status
**Messaging**: POST/GET /room/new, /room/join, /search_users
**Notifications**: POST /notification/mark_read, /notification/delete

## Environment Variables

Required variables (see .env.example):
- FLASK_ENV, SECRET_KEY
- SQLALCHEMY_DATABASE_URI
- REDIS_URL
- MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD

## Directory Structure

```
app/
  api/              # API blueprints (jobs, applications, etc.)
  config/           # Configuration (dev/prod/test)
  models.py         # SQLAlchemy models
  extensions.py     # Flask extensions
  utils/            # Helpers (logging, validation, file handling)
  views/            # Frontend routes
  templates/        # Jinja2 templates
  static/           # CSS, JS, uploads
  sockets/          # WebSocket event handlers
```

## License

See LICENSE file for details.

