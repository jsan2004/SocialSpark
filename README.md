# SocialSpark 🌐

SocialSpark is a microservices-based social networking application built using Python and Flask.

The application allows users to register, log in, manage their profiles, create posts, interact with posts, send friend requests, search for users, and receive notifications.

---

## ✨ Features

- User registration and login
- Password hashing and session-based authentication
- User profile management
- Create and view posts
- Like and interact with posts
- Search for users
- Send and manage friend requests
- Notifications
- Microservices-based architecture
- Central API Gateway
- Server-side rendered frontend using Flask and Jinja2

---

## 🏗️ Architecture

SocialSpark follows a microservices architecture.

```text
                         ┌──────────────────┐
                         │     Frontend     │
                         │   Flask :5000    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    API Gateway   │
                         │   Flask :5004    │
                         └────────┬─────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
     │ User Service │     │ Post Service │     │Friend Service│
     │   :5001      │     │    :5002     │     │    :5003     │
     └──────────────┘     └──────────────┘     └──────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Notification   │
                         │     Service      │
                         └──────────────────┘

Services
Service	Port	Responsibility
Frontend	5000	Web interface and user interaction
User Service	5001	Registration, login and profile management
Post Service	5002	Post creation, retrieval and likes
Friend Service	5003	Friend requests and friendships
API Gateway	5004	Central API entry point and request routing
Notification Service	—	Handles user notifications

Services communicate with each other through HTTP REST APIs.

🛠️ Tech Stack
Backend
Python
Flask
Flask-CORS
Requests
Werkzeug
Frontend
HTML
CSS
JavaScript
Jinja2
Flask
Architecture
Microservices
REST APIs
API Gateway
Session-based authentication
Package Management
pyproject.toml
uv.lock
🔐 Authentication

SocialSpark uses session-based authentication.

The User Service creates a session after successful login. The session identifier is passed between services using the Session-ID HTTP header.

Passwords are stored using Werkzeug password hashing rather than plain-text passwords.

💾 Data Storage

The current version uses in-memory Python data structures for storing application data.

This means:

Data is available while the services are running.
Data is lost when the services restart.
The current implementation is intended for development and testing.

A database can be integrated in a future version.

📁 Project Structure
SocialSpark/
│
├── api_gateway/
│   └── app.py
│
├── user_service/
│   └── app.py
│
├── post_service/
│   └── app.py
│
├── friend_service/
│   └── app.py
│
├── notification_service/
│   └── app.py
│
├── frontend/
│   ├── app.py
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       ├── profile.html
│       ├── edit_profile.html
│       ├── notifications.html
│       └── search_users.html
│
├── start_all_services.py
├── pyproject.toml
├── uv.lock
├── .gitignore
├── replit.md
└── README.md
🚀 Getting Started
Prerequisites

Make sure you have:

Python 3.x
Git
pip or uv
1. Clone the Repository
git clone https://github.com/jsan2004/SocialSpark.git
cd SocialSpark
2. Install Dependencies

The project uses pyproject.toml and uv.lock for dependency management.

Using pip, install the main dependencies:

pip install Flask Flask-CORS requests Werkzeug

Alternatively, if you use uv:

uv sync
3. Start the Application

Run:

python start_all_services.py

This starts the required services on their configured ports.

4. Open the Application

Open the following address in your browser:

http://localhost:5000
🔄 How It Works
The user opens the SocialSpark frontend.
The frontend sends requests to the API Gateway.
The API Gateway routes each request to the appropriate microservice.
The User Service handles authentication and user information.
The Post Service handles posts and post interactions.
The Friend Service manages friendships and friend requests.
The Notification Service handles notifications.
Responses are returned through the API Gateway to the frontend.
⚠️ Current Limitations
Data is stored in memory.
Data is lost when services restart.
Service URLs are currently configured for local development.
No production database is currently configured.
The application is intended primarily for development and educational purposes.
🔮 Future Improvements

Possible future improvements include:

Integrating a relational database
Persistent user and post data
JWT-based authentication
Improved API security
Production deployment
Better error handling and logging
Image storage using cloud storage
Pagination for posts and users
Real-time notifications
Improved service discovery
Automated testing
📌 Project Status

Status: Development / Educational Project

SocialSpark demonstrates how a social networking application can be divided into independent microservices that communicate through REST APIs.

📄 License

This project is available for educational and personal use.