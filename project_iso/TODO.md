# TODO: Real-time Dashboard Refresh + Ticket View Fix

## Steps

1. [x] Add SSE endpoint `/api/stream` and broadcast helper in `routes/api.py`.
2. [x] Hook ticket mutations (create, edit, approve, reject, assign/unassign vehicle) in `routes/tickets.py` to broadcast `ticket_update` events.
3. [x] Add client-side `EventSource` listener in `templates/base.html` to reload page on updates.
4. [x] Fix assigned vehicle visibility in `templates/tickets/view.html` so non-admin users can see it.
5. [ ] Test the app to confirm real-time refresh and vehicle visibility.

