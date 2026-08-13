# Social Network Application

## Overview

This is a microservices-based social network application built with Flask and Python. The system allows users to register, create posts, send friend requests, and interact through a social feed. The application is designed with a service-oriented architecture where different functionalities are separated into independent services that communicate through HTTP APIs.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Microservices Architecture
The application follows a microservices pattern with five main services:

- **User Service (Port 5001)**: Handles user authentication, registration, and profile management using in-memory storage
- **Post Service (Port 5002)**: Manages post creation, retrieval, and interactions like likes
- **Friend Service (Port 5003)**: Handles friend requests and friendship management
- **API Gateway (Port 5004)**: Central entry point that routes requests to appropriate microservices and handles cross-cutting concerns
- **Frontend Service (Port 5000)**: Flask-based web application serving HTML templates and static assets

### Communication Pattern
Services communicate through HTTP REST APIs with the API Gateway acting as a reverse proxy. Session-based authentication is implemented where the User Service validates sessions and other services forward session tokens for authorization.

### Data Storage
Currently uses in-memory storage (Python dictionaries) for all data persistence across all services. This means data is lost when services restart and is suitable only for development/testing.

### Frontend Architecture
Server-side rendered Flask application using Jinja2 templates with minimal client-side JavaScript for interactive features like post liking. The frontend communicates exclusively with the API Gateway rather than directly with individual services.

### Authentication & Authorization
Session-based authentication where:
- Users log in through the User Service which creates a session token
- Session tokens are passed via HTTP headers (`Session-ID`)
- Each protected endpoint validates sessions by calling the User Service
- No JWT or OAuth implementation - simple session validation

### Service Discovery
Static service discovery with hardcoded service URLs (localhost with specific ports). Services are started using a Python orchestration script rather than container orchestration.

## External Dependencies

### Core Framework
- **Flask**: Web framework for all services
- **Flask-CORS**: Cross-origin resource sharing support

### HTTP Client
- **Requests**: Inter-service HTTP communication

### Security
- **Werkzeug**: Password hashing utilities

### Development Tools
- **Python subprocess**: Service orchestration and process management

### Template Engine
- **Jinja2**: Server-side template rendering (included with Flask)

Note: The application currently has no database dependencies and uses no external APIs or cloud services. All data is stored in memory, making it suitable only for development and testing environments.