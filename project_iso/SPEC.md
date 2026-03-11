# Travel Request Ticket Handling System - Specification

## Project Overview
- **Project Name**: City ENRO Travel Request System
- **Type**: Web Application (Flask + MySQL)
- **Core Functionality**: Multi-level approval workflow for travel requests across 8 divisions
- **Target Users**: Employees, Directors, Final Authorizers

## Requirements

### 1. Divisions (8 ENRO Divisions)
- Division 1: Forestry Management Services Division
- Division 2: Wildlife Management Services Division
- Division 3: Protected Area Management Division
- Division 4: Mines and Geosciences Management Service Division
- Division 5: Land Management Services Division
- Division 6: Environmental Management Services Division
- Division 7: Environmental Law Enforcement Division
- Division 8: Administrative Management Services Division

### 2. Approval Workflow
1. **Employee**: Creates travel request for their division
2. **Director Level (2 authorized)**: Can view ALL requests, approve/reject
3. **Final Authorizer**: Final approval after director approval

### 3. User Roles
- **Employee**: Can create/view own requests
- **Director (2)**: Can view all requests, approve/reject at director level
- **Final Authorizer**: Can view all requests, give final approval

### 4. Request Status Flow
- `Pending` → `Director Approved` → `Final Approved` OR `Rejected` (at any stage)

## Technical Stack
- **Backend**: Python, Flask
- **Database**: MySQL
- **Frontend**: HTML/CSS (Bootstrap)
- **Security**: Password hashing, session management, role-based access

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | User ID |
| username | VARCHAR(50) | Username |
| password | VARCHAR(255) | Hashed password |
| role | ENUM | employee, director, final_authorizer |
| division_id | INT (FK) | Division (for employees) |
| full_name | VARCHAR(100) | Full name |

### divisions
| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | Division ID |
| name | VARCHAR(100) | Division name |

### tickets
| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | Ticket ID |
| user_id | INT (FK) | Requester ID |
| division_id | INT (FK) | Division |
| destination | VARCHAR(200) | Travel destination |
| purpose | TEXT | Purpose of travel |
| associates | TEXT | Other travelers |
| start_date | DATE | Travel start date |
| end_date | DATE | Travel end date |
| vehicle_needed | VARCHAR(10) | Vehicle needed (yes/no) |
| vehicle_assigned | VARCHAR(100) | Vehicle assigned (admin only) |
| status | ENUM | pending, director_approved, approved, rejected |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update |

### approvals
| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | Approval ID |
| ticket_id | INT (FK) | Ticket ID |
| approver_id | INT (FK) | Approver user ID |
| level | ENUM | director, final |
| action | ENUM | approved, rejected |
| comments | TEXT | Approval comments |
| created_at | DATETIME | Approval timestamp |

## API Endpoints

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout

### Tickets
- `GET /` - Dashboard (role-based)
- `GET /tickets` - List tickets (role-based)
- `POST /tickets` - Create new ticket
- `GET /tickets/<id>` - View ticket details
- `POST /tickets/<id>/approve` - Approve ticket
- `POST /tickets/<id>/reject` - Reject ticket

### Users (Admin)
- `GET /users` - List users
- `POST /users` - Create user

## Security Considerations
1. Password hashing (bcrypt)
2. Session-based authentication
3. Role-based access control (RBAC)
4. Input validation and sanitization
5. CSRF protection
6. SQL injection prevention (parameterized queries)

