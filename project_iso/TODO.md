# CITY HALL TICKET SYSTEM - INCREASE /TICKETS/ VIEW WIDTH

## Approved Plan Steps
**Status: In Progress**

1. [x] Create TODO.md with breakdown ✅
2. [x] Update base.html: Replace .container with .container-fluid + custom .wide-container (max-width: 1600px) ✅
3. [x] Update all_tickets.html: Wrap table card in .wide-container class ✅
4. [x] Update my_tickets.html: Wrap table card in .wide-container class ✅ 
5. [x] Update view.html: Adjust columns to col-lg-9 / col-lg-3 + .wide-container ✅
6. [x] Add responsive CSS in base.html: Adjust paddings, table column min-widths ✅
7. [ ] Test: cd project_dir/Ticket_Handler_City_Hall/project_iso && flask run
8. [ ] Verify: Wider tables on desktop, responsive mobile

**Target:** +40% width on desktop (1140px → 1600px), full fluid below 1200px.

**Test URLs:** 
- http://127.0.0.1:5000/tickets/ (all_tickets or my_tickets)
- http://127.0.0.1:5000/tickets/<id> (view.html)

## CENTER TRAVEL REQUEST TITLE AND CARD
**Status: Planning**

1. [ ] Append centering plan to TODO.md ✅
2. [x] Update tickets/view.html: Integrate row justify-content-center col mb-6 snippet, wrap main col-lg-9 card in col-lg-8 mx-auto ✅
3. [x] Update tickets/create.html: Title col-12 → col-lg-8 mx-auto text-center; main col-md-8 → col-lg-8 mx-auto ✅
4. [x] Update tickets/edit.html: Same as create.html ✅
5. [x] Test pages: /tickets/create, /tickets/ID, /tickets/edit/ID ✅

**Status: Complete**

## MOVE TRAVEL REQUEST NUMBER TO CARD BODY
**Status: Complete**

1. [x] view.html/edit.html: Move #{{ ticket.id }} from header to prominent position in card-body (h4 fw-bold with border) ✅
2. [x] Headers restored to "Request Details"/"Travel Details" ✅
3. [x] Test verified (app running, /tickets/8 visited) ✅

## ADMIN USER MANAGEMENT & PASSWORD CHANGE SYSTEM
**Status: Complete** ✅

**High-Level Goal:** 
- Remove public self-registration 
- Admin-only user creation (employee accounts)
- Self-service password change for all users
- Enhance vehicle status (already partially exists)
- Add status column in tickets/vehicles views

**Files to Edit/Create:**
| Category | Files |
|----------|-------|
| Remove Register | templates/auth/login.html, templates/auth/register.html, routes/auth.py |
| Admin Users | new templates/admin/users.html, routes/main.py or new admin.py, _navbar.html (admin link) |
| Password Change | new templates/account/settings.html, routes/auth.py or main.py, _navbar.html |
| Vehicles | templates/tickets/vehicles.html (status edit OK), tickets.py logic |
| Tickets Status | templates/tickets/all_tickets.html, my_tickets.html (add vehicle_status <td>) |

**Detailed Steps:**
1. [x] **Remove Public Register** 
   - templates/auth/login.html: Remove 'Register as Employee' link → 'Contact admin' ✅
   - templates/auth/register.html: Replace form → static 'Admin creates accounts' ✅
   - routes/auth.py: /register → flash('Admin-only') + redirect login ✅

2. [x] **Admin Create User** (role=employee, temp pw 'change123', force change on login)
   - Create templates/admin/users.html (table list + add form: username, full_name, division_id) ✅
   - Add route main.admin_users() (admin-only) ✅
   - _navbar.html: Admin nav link 'Manage Users' ✅

3. [x] **Account Settings** (password change, all roles)
   - Create templates/account/settings.html (old/new/confirm pw form) ✅
   - Add route main.account_settings() ✅
   - _navbar.html: User dropdown 'Settings' ✅

4. [x] **Vehicle Status** (enhance)
   - templates/tickets/vehicles.html: Already has status column/edit buttons ✅
   - Ensure ticket views show vehicle_status if assigned (queries updated) ✅

5. [x] **Tickets Status Column**
   - all_tickets.html, my_tickets.html: Add <th>Vehicle Status</th> + <td>{{ ticket.vehicle_status|title or '-' }}</td> ✅

**Dependencies:** No DB schema change (users table exists). Test roles: admin creates employee → employee changes pw.

**Test Plan:**
- Admin login → Manage Users → create employee (temp pw)
- Employee login (temp) → force change pw → settings works
- Vehicles page: status toggle
- Tables: vehicle_status shows

**Expected Completion:** 15-20 file changes across templates/routes/navbar.
