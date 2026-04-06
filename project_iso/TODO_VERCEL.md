# Vercel Deployment - Complete Step-by-Step

1. [x] requirements.txt updated
2. [x] .env.example created

## Step-by-Step Deployment (Windows/PowerShell)

### Step 1: Install Vercel CLI
```
npm install -g vercel
```
(Install Node.js from nodejs.org if npm not found)

### Step 2: Navigate & Login
```
cd "c:/Users/Niiyyoooww/Desktop/CITY_HALL_ASSIGNMENT/project_dir/Ticket_Handler_City_Hall/project_iso"
vercel login
```
(Follow browser auth)

### Step 3: Install Deps (already done)
```
cvenv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Local Test (optional)
```
vercel dev
```
(Open http://localhost:3000)

### Step 5: Deploy
```
vercel --prod
```
- Link to new project when prompted (yes)
- Framework: Other
- Root: . (current)

### Step 6: Set SECRET_KEY
- Go to vercel.com/dashboard → Your Project → Settings → Environment Variables
- Add: `SECRET_KEY` = `sk-your-super-secret-key-generate-one`
- Redeploy: `vercel --prod`

### Step 7: Test
- Visit deployed URL
- Login: admin / admin123

**Fixed:** app.py now exports top-level `app` for Vercel.

**404 Fix:** 
1. Redeploy after edit: `vercel --prod`
2. Check Functions log
3. SECRET_KEY required

**Prod DB:** planetscale.com free MySQL + set MYSQL_* vars.

Ready! Run Step 1-5 now.
