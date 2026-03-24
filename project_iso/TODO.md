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

