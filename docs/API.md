# API Documentation

## Base URL
- Development: `http://localhost:8000/api`
- Production: `https://assistant.uottawa.ca/api`

## Authentication

All endpoints require JWT authentication via uOttawa SSO.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## Endpoints

### Authentication
- `POST /auth/login` - SSO login
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout

### Chat
- `POST /chat/message` - Send message
- `GET /chat/history` - Get chat history
- `DELETE /chat/history` - Clear history

### Courses
- `GET /courses` - Get user's courses
- `GET /courses/{course_id}` - Get course details
- `GET /courses/{course_id}/grades` - Get grades

### Users
- `GET /users/me` - Get current user
- `PUT /users/me` - Update user preferences

For detailed schemas, see the interactive docs at `/docs` when running the server.
