# TODO - Add Associates Field to Tickets

## Progress Tracker

- [x] 1. Update routes/tickets.py - Add associates field handling in create route
- [x] 2. Update templates/tickets/create.html - Add associates input field
- [x] 3. Update templates/tickets/view.html - Display associates in ticket details
- [x] 4. Update templates/tickets/all_tickets.html - Add Associates column to table
- [x] 5. Update templates/tickets/my_tickets.html - Add Associates column to table
- [x] 6. Add vehicle_needed and vehicle_assigned fields to routes and templates
- [x] 7. Add edit route for tickets

## Notes
- Database already has `associates VARCHAR(200) NOT NULL` column in tickets table (MySQL)
- For SQLite, run migrations to add the columns:
  - `associates VARCHAR(200)`
  - `vehicle_needed VARCHAR(10) DEFAULT 'no'`
  - `vehicle_assigned VARCHAR(100)`
