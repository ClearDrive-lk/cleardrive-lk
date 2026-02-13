# ClearDrive.lk - Vehicle Import Platform
Check
## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Setup (5 minutes)
```bash
# Clone repository
git clone https://github.com/cleardrive-lk/cleardrive.git
cd cleardrive

# Start all services
docker-compose up -d

# Initialize database (first time only)
docker-compose exec backend python scripts/init_db.py

# Access API
# - API: http://localhost:8000
# - Swagger Docs: http://localhost:8000/api/v1/docs
# - ReDoc: http://localhost:8000/api/v1/redoc
```

## 📚 API Documentation

### Base URL
```
Development: http://localhost:8000/api/v1
```

### Authentication Flow

#### 1. Google OAuth Login
```http
POST /auth/google
Content-Type: application/json

{
  "id_token": "google-id-token-from-client"
}

Response: 200 OK
{
  "email": "user@example.com",
  "name": "John Doe",
  "google_id": "123456789",
  "message": "OTP sent to email"
}
```

#### 2. Verify OTP
```http
POST /auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}

Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "CUSTOMER",
    "created_at": "2026-01-26T10:00:00Z"
  }
}
```

#### 3. Use Access Token
```http
GET /vehicles
Authorization: Bearer eyJhbGc...
```

#### 4. Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}

Response: 200 OK
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  ...
}
```

### Vehicle Endpoints

#### List Vehicles (Public)
```http
GET /vehicles?search=Toyota&fuel_type=HYBRID&page=1&limit=20

Response: 200 OK
{
  "vehicles": [
    {
      "id": "uuid",
      "make": "Toyota",
      "model": "Prius",
      "year": 2020,
      "price_jpy": 1850000,
      "mileage_km": 35000,
      "fuel_type": "HYBRID",
      "transmission": "AUTOMATIC",
      "status": "AVAILABLE",
      ...
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20,
  "total_pages": 3
}
```

**Query Parameters:**
- `search` - Search in make/model
- `make` - Filter by manufacturer
- `model` - Filter by model
- `year_min` / `year_max` - Year range
- `price_min` / `price_max` - Price range (JPY)
- `mileage_max` - Maximum mileage
- `fuel_type` - PETROL, DIESEL, HYBRID, ELECTRIC, CNG
- `transmission` - MANUAL, AUTOMATIC, CVT, SEMI_AUTOMATIC
- `status` - AVAILABLE, RESERVED, SOLD, UNAVAILABLE
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)
- `sort_by` - price_jpy, year, mileage_km, created_at
- `sort_order` - asc, desc

#### Get Vehicle Details (Public)
```http
GET /vehicles/{vehicle_id}

Response: 200 OK
{
  "id": "uuid",
  "make": "Toyota",
  "model": "Prius",
  "year": 2020,
  "price_jpy": 1850000,
  ...
}
```

#### Calculate Import Cost (Public)
```http
GET /vehicles/{vehicle_id}/cost?exchange_rate=2.25

Response: 200 OK
{
  "vehicle_price_jpy": 1850000,
  "vehicle_price_lkr": 4162500.00,
  "exchange_rate": 2.25,
  "shipping_cost_lkr": 180000.00,
  "customs_duty_lkr": 2081250.00,
  "excise_duty_lkr": 1085625.00,
  "vat_lkr": 1129106.25,
  "cess_lkr": 0.00,
  "port_charges_lkr": 25000.00,
  "clearance_fee_lkr": 35000.00,
  "documentation_fee_lkr": 15000.00,
  "total_cost_lkr": 8713481.25,
  "vehicle_percentage": 47.8,
  "taxes_percentage": 49.3,
  "fees_percentage": 2.9
}
```

### Session Management

#### Get All Sessions (Authenticated)
```http
GET /auth/sessions
Authorization: Bearer {access_token}

Response: 200 OK
{
  "sessions": [
    {
      "id": "uuid",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "device_info": "Desktop",
      "location": "Colombo, LK",
      "is_active": true,
      "last_active": "2026-01-26T10:00:00Z",
      "created_at": "2026-01-26T09:00:00Z"
    }
  ],
  "total": 2,
  "current_session_id": "uuid"
}
```

#### Revoke Session (Authenticated)
```http
DELETE /auth/sessions/{session_id}
Authorization: Bearer {access_token}

Response: 200 OK
{
  "message": "Session revoked successfully"
}
```

#### Logout (Authenticated)
```http
POST /auth/logout
Authorization: Bearer {access_token}

Response: 200 OK
{
  "message": "Logged out successfully"
}
```

## 🔐 User Roles & Permissions

### CUSTOMER
- Browse vehicles
- Create orders
- Submit KYC
- View own orders/payments
- Request finance/insurance

### ADMIN
- All permissions
- Manage users
- Approve KYC
- Assign exporters
- View audit logs

### EXPORTER
- View assigned orders
- Upload shipping documents
- Update shipping details

### CLEARING_AGENT
- Manage customs clearance
- Upload customs documents

### FINANCE_PARTNER
- View finance requests
- Approve/reject finance applications

## 🧪 Testing

### Test Credentials (Development)
```
Admin: malith@cleardrive.lk (auto-created on first run)
```

### Sample Vehicles
20 vehicles auto-created on initialization:
- Toyota Prius, Aqua, Vitz, Corolla Axio
- Honda Fit, Vezel, Grace
- Nissan Leaf, Note, Serena
- Mazda Demio, Axela
- And more...

## 📁 Project Structure
```
cleardrive/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── core/         # Config, database, security
│   │   ├── modules/      # Domain modules (auth, vehicles, etc.)
│   │   └── main.py       # FastAPI app
│   ├── scripts/          # Utility scripts
│   └── alembic/          # Database migrations
├── apps/
│   ├── web/              # Next.js frontend (TODO)
│   └── mobile/           # React Native app (TODO)
├── packages/
│   └── shared/           # Shared code (TODO)
└── docker-compose.yml
```

## 🔧 Development

### Backend
```bash
# Watch logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Run tests
docker-compose exec backend pytest

# Access Python shell
docker-compose exec backend python
```

### Database
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d cleardrive

# Common commands:
\dt              # List tables
\d users         # Describe table
\q               # Quit
```

### Redis
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Common commands:
KEYS *           # List all keys
GET otp:email    # Get value
TTL key          # Time to live
```

## 🚀 Deployment (TODO)

- Frontend: Vercel
- Backend: Railway/Render
- Database: Supabase
- Redis: Redis Cloud
- CDN: Cloudflare

## 📝 Environment Variables

See `.env.example` files in:
- `backend/.env.example` - Backend configuration
- `apps/web/.env.local.example` - Frontend configuration (TODO)

## 🤝 Contributing

1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Create Pull Request

### Commit Convention
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Tests
- `chore:` - Maintenance

## 📞 Team

- Malith - Technical Lead / Backend
- Lehan - Frontend Lead
- Tharin - Orders / Payments
- Pavara - KYC / AI
- Parindra - Vehicles / Security Docs
- Kalidu - Shipping / GDPR

## 📄 License

MIT
