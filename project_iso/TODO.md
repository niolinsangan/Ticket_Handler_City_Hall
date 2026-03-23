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
