# PythonAnywhere Deployment Guide

## Your requirements.txt is complete!
All required modules are already included:
- Flask==3.0.0
- Flask-Bcrypt==1.0.1
- Flask-WTF==1.2.1
- WTForms==3.1.1
- python-dotenv==1.0.0
- PyMySQL==1.1.0
- cryptography==41.0.7

---

## Step-by-Step Deployment to PythonAnywhere

### Step 1: Create PythonAnywhere Account
1. Go to https://www.pythonanywhere.com/
2. Click "Register" to create an account
3. Choose the free tier to start

### Step 2: Upload Your Code
1. Log in to PythonAnywhere
2. Go to **Files** tab
3. Navigate to `/home/yourusername/`
4. Create a folder named `cityhall`
5. Upload all files from your `project_iso` folder to `/home/yourusername/cityhall/`

### Step 3: Create MySQL Database
1. Go to **Databases** tab
2. Create a new MySQL database
   - Database name: `cityhall$default` (or your choice)
   - Username and password: Note these down
3. Initialize the database by running in Bash console:
   ```
   cd /home/yourusername/cityhall
   python
   from app import app, init_db
   app.app_context().push()
   init_db(app)
   ```

### Step 4: Configure Web App
1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.12** (or latest available)

### Step 5: Set Environment Variables
In the **Web** tab, scroll to **Environment variables** and add:
```
SECRET_KEY=generate-a-secure-random-string-here
MYSQL_HOST=yourusername.mysql.pythonanywhere-services.com
MYSQL_USER=your-pythonanywhere-username
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=your-database-name
```

### Step 6: Install Dependencies
Open a **Bash console** and run:
```bash
pip install --user -r /home/yourusername/cityhall/requirements.txt
```

### Step 7: Configure WSGI File
Edit the WSGI file (click the link in Web tab) and replace content with:

```python
import sys

# Add your project directory to the path
path = '/home/yourusername/cityhall'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
import os
os.environ['SECRET_KEY'] = 'your-secret-key'
os.environ['MYSQL_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['MYSQL_USER'] = 'yourusername'
os.environ['MYSQL_PASSWORD'] = 'your-password'
os.environ['MYSQL_DATABASE'] = 'yourusername$default'

# Run the Flask app
from app import app as application
```

### Step 8: Reload the App
1. Go to **Web** tab
2. Click **Reload** button
3. Visit your app at `https://yourusername.pythonanywhere.com`

---

## Default Login Credentials
After first run, use:
- **Username:** admin
- **Password:** admin123

---

## Troubleshooting
- Check **Error log** in Web tab if issues occur
- Make sure database is created and initialized
- Verify environment variables are set correctly

