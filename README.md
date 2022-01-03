# Reunion Planner
### Final Project for Harvard's CS50 and to practice my newly learned skills
#### Video Demo:  [Reunion Planner on Youtube] (https://youtu.be/H1kr_UDd4LM)


## Description for user:

**Ever want to schedule a meetup with friends or colleagues but you keep exchanging possible dates and availabilities? This application makes it easier for you!**
Just enter the persons you want to invite, pick some dates you want to suggest to your friends from the date list.
Then let your friends log in and click their availability for these dates and voila: 
you will be presented a clear visual representation of all availabilities which leaves you an easy job setting the final date.

![image info](screenshots/login_dt.png)
![image info](screenshots/index_dt.png)
![image info](screenshots/availability_dt.png)
![image info](screenshots/reunion_dt.png)


## Technical

The application is written with following techniques:
Python, Flask, Jinja, SQLite3, JavaScript, Bootstrap, JQuery, HTML, CSS.

Dependencies with:
flask, flask_session, 
werkzeug.security (check_password_hash, generate_password_hash)
tempfile
datetime
sqlite3

Future features (not built in yet): 
- have invitations sent by email.

### SQLite3 Database
The SQLite3 database and tables will be made and initially populated automatically by running the application's Python code.

### Python Files

**application.py**
- Enholds almost the full application.
- Here libraries are being linked/loaded.
- A new SQLite3 database is created, and functions are being called to make the database tables, and to populate the table with dates.
- It will start running the webapplication.
- It will handle and route most user actions with Flask, and routes to html pages.

**dbsetup.py**
- Is being called by application.py
- Enholds the functions to create necessary database tables and to populate the date table with dates


### HTML/CSS Files
These pages use Bootstrap and Jinja.

**layout.html**
Is the overall template of the other .html pages, and enholds the:
- html header
- login and signup validity check scripts
- navigation bar
- outer building blocks of the website.
- placeholder for the code of the other .html pages as described below

**login.html**
Page where the user is directed to if not logged in.
It is both for signing up and for logging in.
Validity check on the page for:
- fields not being empty, correct email format, password confirmation equal to password

**index.html**
Shows the list of reunions:
- Two different html tables are being made, one for reunions made and one for reunions invited to.
- Each row will indicate a reunion title, creator and status (invited, need your availability, final date set).
- Each row links to its specific reunion page (or to an availability.html page).

**new.html**
Will let the user (in this case: organiser) step by step:
- enter a title
- enter all emailaddresses of invitees
- pick suggestion dates from a list of dates.

**availability.html**
Lets invitees give their availability for a reunion, by checking for each suggested date one of 3 radiobuttons:
- yes, no or mwah.

**reunion.html**
Shows both organiser and invitees a matrix view of
- dates
- invitees
- filled in with colored blocks indicating the availability.
To the organiser radiobuttons are available to pick a final date for this reunion.

**styles.css**
Extra styling to:
- Make full table rows clickable
- Enable table header to show text rotated








