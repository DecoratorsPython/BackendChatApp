# Real-Time Chat Application

A lightweight, containerized backend service enabling real‑time
messaging between users authenticated through Google OAuth.\
This service powers friend discovery, real-time chat and audio‑enabled
messages using a modern, scalable architecture.

------------------------------------------------------------------------

## 🚀 Features

### **Authentication & Security**

-   **Google OAuth 2.0** for seamless and secure login.
-   **JWT-based session management** to authorize all API and WebSocket
    operations.

### **Friendship System**

-   Send friend requests by email address.
-   Accept or decline incoming friend requests.
-   View **suggested friends** based on mutual connections.

### **Real-Time Messaging**

-   Bi‑directional, real‑time communication powered by **WebSockets**.
-   Messages are instantly synchronized between two users.
-   Text-to-speech (Web Speech API).

### **Production-Ready Workflow**

-   Fully containerized backend & database using **Docker**.
-   Built with **FastAPI**, ensuring high performance and clean
    architecture.
-   Persisted storage and relational modeling using **PostgreSQL**.

------------------------------------------------------------------------

## 🛠️ Technologies Used
| Category                | Technologies                     |
|-------------------------|----------------------------------|
| **Language**            | Python                           |
| **Framework**           | FastAPI                          |
| **Real-Time Transport** | WebSockets                       |
| **Database**            | PostgreSQL                       |
| **Authentication**      | Google OAuth 2.0, JWT            |
| **Containerization**    | Docker                           |


------------------------------------------------------------------------

## 🧩 High-Level Architecture

    Client ↔ FastAPI Backend ↔ PostgreSQL
              ↕
             WebSocket

-   REST endpoints manage authentication, profiles, friendships and
    message history.
-   WebSockets allow instantaneous delivery of messages.
-   PostgreSQL maintains users, friendships and message metadata.

------------------------------------------------------------------------

## ▶️ Running the Project

### **Prerequisites**

-   Docker installed
-   Google OAuth credentials (Client ID & Secret)

### **Environment Variables**

Create an `.env` file in the project root:

    google_client_id=YOUR_GOOGLE_CLIENT_ID
    google_client_secret=YOUR_GOOGLE_CLIENT_SECRET
    google_redirect_url=http://localhost:8000/dev/auth/google/callback
    session_secret_key=your-very-secret-key
    DATABASE_URL=your-database-url
    JWT_SECRET=your-jwt-secret
    JWT_ALGORITHM=HS256
    ACCESS_TOKEN_TTL_SECONDS=600
    REFRESH_TOKEN_TTL_DAYS=30
    frontend_root_url=http://localhost:5173
    DATABASE_NAME=your-database-name
    DATABASE_USER=your-database-username
    DATABASE_PASSWORD=your-database-password

### **Start the Backend**

``` sh
docker-compose up --build
```

The FastAPI server will be available at:

    http://localhost:8000
