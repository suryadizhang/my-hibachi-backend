# My Hibachi - Backend API

FastAPI-based backend service for My Hibachi's premium hibachi catering platform, providing robust API endpoints for booking management, user authentication, and business operations.

## 🚀 Features

- **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- **SQLAlchemy ORM**: Database management with Alembic migrations
- **Authentication**: JWT-based user authentication and authorization
- **Email Integration**: Automated booking confirmations and notifications
- **Payment Processing**: Stripe integration for secure payments
- **Admin Dashboard**: Comprehensive booking and user management
- **API Documentation**: Auto-generated Swagger/OpenAPI docs

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **Email**: SMTP integration
- **Testing**: Pytest
- **Deployment**: Docker ready

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/my-hibachi-backend.git
   cd my-hibachi-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   ```bash
   cp .env.example .env
   ```
   
   Update `.env` with your configuration:
   ```env
   DATABASE_URL=sqlite:///./mh-bookings.db
   SECRET_KEY=your-super-secret-key-here
   CORS_ORIGINS=["http://localhost:5173", "https://your-frontend-domain.com"]
   
   # Email Configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASS=your-app-password
   
   # Stripe (Optional)
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```

5. **Database Setup**
   ```bash
   # Initialize database
   alembic upgrade head
   
   # Create superuser (optional)
   python -m app.create_superadmin
   ```

6. **Start development server**
   ```bash
   uvicorn main:app --reload
   ```

## 🏗️ Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration
├── models/              # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── booking.py
│   └── ...
├── routes/              # API route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── bookings.py
│   ├── admin.py
│   └── ...
├── services/            # Business logic
│   ├── __init__.py
│   ├── booking_service.py
│   ├── email_service.py
│   └── ...
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── security.py
│   ├── email_utils.py
│   └── ...
└── schemas/             # Pydantic models
    ├── __init__.py
    ├── user.py
    ├── booking.py
    └── ...

tests/                   # Test files
├── __init__.py
├── conftest.py
├── test_auth.py
├── test_bookings.py
└── ...

alembic/                 # Database migrations
├── versions/
├── env.py
└── alembic.ini
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_bookings.py

# Run tests in verbose mode
pytest -v
```

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token
- `GET /auth/me` - Get current user info

### Bookings
- `GET /bookings/` - List all bookings
- `POST /bookings/` - Create new booking
- `GET /bookings/{booking_id}` - Get booking details
- `PUT /bookings/{booking_id}` - Update booking
- `DELETE /bookings/{booking_id}` - Cancel booking

### Admin
- `GET /admin/bookings/` - Admin booking management
- `GET /admin/users/` - User management
- `GET /admin/analytics/` - Business analytics

### Public
- `GET /` - Health check
- `GET /menu/` - Get menu items
- `POST /contact/` - Contact form submission

## 🔒 Authentication

The API uses JWT (JSON Web Tokens) for authentication:

```python
# Protected endpoint example
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}
```

## 🗄️ Database Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Booking Model
```python
class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_date = Column(DateTime)
    guest_count = Column(Integer)
    total_cost = Column(Float)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 📧 Email Integration

The system sends automated emails for:
- Booking confirmations
- Payment receipts
- Reminder notifications
- Admin notifications

```python
# Email service example
async def send_booking_confirmation(booking: Booking, user: User):
    subject = f"Booking Confirmation - My Hibachi #{booking.id}"
    template = "booking_confirmation.html"
    await email_service.send_email(user.email, subject, template, booking)
```

## 🚢 Deployment

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production with Docker
```bash
# Build image
docker build -t my-hibachi-backend .

# Run container
docker run -p 8000:8000 --env-file .env my-hibachi-backend
```

### Deploy to Railway (Recommended)
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main branch

### Deploy to Heroku
```bash
# Install Heroku CLI and login
heroku create my-hibachi-backend
heroku config:set DATABASE_URL="your-postgres-url"
heroku config:set SECRET_KEY="your-secret-key"
git push heroku main
```

## 🌐 Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `DATABASE_URL` | Database connection string | Yes | `sqlite:///./mh-bookings.db` |
| `SECRET_KEY` | JWT secret key | Yes | `your-super-secret-key` |
| `CORS_ORIGINS` | Allowed CORS origins | Yes | `["http://localhost:5173"]` |
| `SMTP_SERVER` | Email SMTP server | No | `smtp.gmail.com` |
| `SMTP_PORT` | Email SMTP port | No | `587` |
| `EMAIL_USER` | Email username | No | `your-email@gmail.com` |
| `EMAIL_PASS` | Email password | No | `your-app-password` |
| `STRIPE_SECRET_KEY` | Stripe secret key | No | `sk_test_...` |

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Commit changes: `git commit -am 'Add new feature'`
6. Push to branch: `git push origin feature/new-feature`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Email: dev@myhibachi.com
- Issues: [GitHub Issues](https://github.com/your-username/my-hibachi-backend/issues)
- API Documentation: `http://localhost:8000/docs` (when running locally)

## 🗺️ Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Advanced payment processing
- [ ] Multi-tenant support
- [ ] Analytics and reporting
- [ ] Mobile app API endpoints
- [ ] Third-party integrations (calendars, CRM)

---

Built with ❤️ for My Hibachi by the development team.
