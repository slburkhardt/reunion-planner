import os
import datetime
import re
import sqlite3
import dbsetup

from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp

#from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

connection = sqlite3.connect("reunionplanner.db", check_same_thread=False)
cursor = connection.cursor()

dbsetup.checkTableExist("users")
dbsetup.checkTableExist("dates")
dbsetup.checkTableExist("reunions")
dbsetup.checkTableExist("invitees")
dbsetup.checkTableExist("datesuggestions")
dbsetup.checkTableExist("availabilities")
# dbsetup.populateTable("dates")


@app.route('/index')
@app.route('/')
def index():
    """ OVERVIEW OF USER'S REUNIONS """
    user = session.get("user_id")
    if session.get("user_id") is None:
        return redirect("login")

    # Get reunions organised by user
    organised = cursor.execute(
        "SELECT id, title, organiser, status, planned_date FROM reunions WHERE organiser = ? AND (status = ? OR status = ?)", (user, 'areinvited', 'scheduled')).fetchall()

    # Get reunions user is invited for
    query = """SELECT reunions.id, reunions.title, reunions.organiser, invitees.status, reunions.status, reunions.planned_date
            FROM reunions
            JOIN invitees ON invitees.reunion_id = reunions.id
            WHERE invitees.email = ? AND (reunions.status = ? OR reunions.status = ?)"""
    invitedfor = cursor.execute(query, (user, 'areinvited', 'scheduled')).fetchall()

    # Show the overview page
    return render_template("index.html", user=user, organised=organised, invitedfor=invitedfor)


@app.route("/login", methods=["GET", "POST"])
def login():
    """ SIGNUP AND LOGIN  """
    user = session.get("user_id")
    inviteesnumber = 0

    if request.method == "GET":
        message = "form not sent"
        return render_template("login.html", message=message, user=user)

    elif request.method == "POST":
        """ SIGNUP """
        if 'signup' in request.form:

            # email checks
            signupemail = request.form.get("signup_email")
            if not signupemail or signupemail == "":
                messagesignup = "Please fill in a correct emailaddress"
                return render_template("login.html", messagesignup=messagesignup, signupemail=signupemail)

            # email exists check and status check (invited or account)
            signupemail = signupemail.lower()
            dbStatusIsInvited = False
            query = "SELECT status FROM users WHERE email = '" + signupemail + "'"
            checkresult = cursor.execute(query).fetchall()

            if checkresult != [] and checkresult[0][0] == "account":
                messagesignup = "This account already exists"
                return render_template("login.html", messagesignup=messagesignup, signupemail=signupemail)
            if checkresult != [] and checkresult[0][0] != "account":
                dbStatusIsInvited = True

            # password fields checks
            password = request.form.get("signup_password")
            confirmPassword = request.form.get("signup_confirmpassword")
            messagesignup = ""
            if not password or password == "":
                messagesignup = "Please fill in your password"
            elif not confirmPassword or confirmPassword == "":
                messagesignup = "Please confirm your password"
            elif password != confirmPassword:
                messagesignup = "Please fill in matching passwords"
            if messagesignup != "":
                return render_template("login.html", messagesignup=messagesignup, signupemail=signupemail)

            # password hashing
            hashkey = generate_password_hash(password)

            # register in database (or: update database if email was registered but not account made)
            if dbStatusIsInvited:
                query = 'UPDATE users SET status = ?, hashkey = ? WHERE email == ?'
                cursor.execute(query, ("account", hashkey, signupemail))
                connection.commit()
            else:
                query = 'INSERT INTO users (email, status, hashkey) VALUES (?,?,?)'
                cursor.execute(query, (signupemail, "account", hashkey))
                connection.commit()

            # get user signed in for session
            session["user_id"] = signupemail

            # redirect user to home page
            return redirect("/")

        elif 'login' in request.form:
            """ LOGIN """

            # forget user_id in session
            session.clear()

            # check if fields filled in properly, if not return with message
            loginemail = request.form.get("login_email")
            if not loginemail or loginemail == "":
                messagelogin = "Please fill in a correct emailaddress"
                return render_template("login.html", messagelogin=messagelogin, loginemail=loginemail)
            loginpassword = request.form.get("login_password")
            if not loginpassword or loginpassword == "":
                messagelogin = "Please fill in your password"
                return render_template("login.html", messagelogin=messagelogin, loginemail=loginemail)

            loginemail = loginemail.lower()

            # check if account exists in db (with status "account"), if not return with message
            query = "SELECT status, hashkey FROM users WHERE email = '" + loginemail + "'"
            checkresult = cursor.execute(query).fetchall()
            if checkresult == [] or checkresult[0][0] != "account":
                messagelogin = "Please signup first!"
                return render_template("login.html", messagelogin=messagelogin, loginemail=loginemail)

            # check if password is correct, if so: login and redirect to homepage
            if check_password_hash(checkresult[0][1], request.form.get("login_password")):
                session["user_id"] = loginemail
                return redirect("/")
            # if not password incorrect return to page with message
            else:
                messagelogin = "Your password... it seems to be wrong?"
                return render_template("login.html", messagelogin=messagelogin, loginemail=loginemail)

        # send back to login page with message
        message = "sent and received"
        return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    """ LOGGING OUT USER """

    # forget user_id in session
    session.clear()

    # redirect user to login form
    return redirect("/login")


@app.route("/new", methods=["GET", "POST"])
def new():
    """ CREATING A NEW REUNION """
    user = session.get("user_id")
    inviteesnumber = 0

    # Make sure user is logged in
    if user is None:
        return redirect("/login")

    if request.method == "GET":
        """ SHOW TITLE ENTRY FIELD """
        message = "form not sent"
        status = "start"

        return render_template("new.html", message=message, user=user, status=status, inviteesnumber=inviteesnumber)

    if request.method == "POST":
        message = "form received"
        if 'givetitle' in request.form:
            """ TITLE ENTERED (SAVE IT) - SHOW INVITEE ENTRY FIELD """

            # save new reunion to db.reunion
            title = request.form.get("title")
            if not title or title == "" or len(title) > 50:
                messagecreate = "Please fill in a title, max 50"
                status = "start"
                return render_template("new.html", messagecreate=messagecreate, message=message, user=user, status=status, inviteesnumber=inviteesnumber)
            query = 'INSERT INTO reunions (title, organiser, status) VALUES (?,?,?)'
            cursor.execute(query, (title, user, "creating"))
            connection.commit()

            # get reunion_id
            reunion_id = cursor.lastrowid
            status = "created"
            return render_template("new.html", message=message, user=user, status=status, reunion_id=reunion_id, title=title, inviteesnumber=inviteesnumber)

        elif 'invitee' in request.form:
            """ INVITEE ENTERED (SAVE IT) - SHOW ANOTHER INVITEE ENTRY FIELD """
            # get form input
            status = "invites"
            messageinvitee = ""
            reunion_id = request.form.get("reunion_id")

            # check form input, if not valid return with message
            invitee = request.form.get("invite")
            if not invitee or invitee == "":
                message = "Please fill in a correct emailaddress"
                return render_template("new.html", messageinvitee=messageinvitee, message=message, user=user, status=status, reunion_id=reunion_id, inviteesnumber=inviteesnumber)

            # check if emailaddress already listed for this reunion
            query = "SELECT email FROM invitees WHERE email = ? and reunion_id = ?"
            checkresult = cursor.execute(query, (invitee, reunion_id,)).fetchall()
            if checkresult != []:
                inviteesmessage = "{} was already on the list of invitees".format(invitee)
                # return render_template("new.html", message=message, user=user, status=status, reunion_id=reunion_id, inviteesnumber=inviteesnumber)

            else:
                # if not yet listed write emailaddress to db.invitees
                query = 'INSERT INTO invitees (reunion_id, email, status) VALUES (?,?,?)'
                cursor.execute(query, (reunion_id, invitee, "listed"))
                connection.commit()
    
                # write emailadress to db.users if not yet there
                query = "SELECT email FROM users WHERE email = ?"
                checkresult = cursor.execute(query, (invitee,)).fetchall()
                if checkresult == []:
                    # write to db
                    query = 'INSERT INTO users (email, status) VALUES (?,?)'
                    cursor.execute(query, (invitee, "invited"))
                    connection.commit()
                else:
                    print("emailaddress {} already exists in db.user".format(invitee))
    
                # change status in db.reunions to addinginvitees
                query = 'UPDATE reunions SET status = ? WHERE id == ?'
                cursor.execute(query, ("addinginvitees", reunion_id))
                connection.commit()

            # get title
            query = "SELECT title FROM reunions WHERE id = ?"
            checkresult = cursor.execute(query, (reunion_id,)).fetchall()
            title = checkresult[0][0]

            # get invitees so far
            query = "SELECT email FROM invitees WHERE reunion_id = ?"
            invitees = cursor.execute(query, (reunion_id,)).fetchall()

            # get number of invitees so far
            query = "SELECT COUNT(email) FROM invitees WHERE reunion_id = ?"
            inviteesnumber = cursor.execute(query, (reunion_id,)).fetchall()
            inviteesnumber = inviteesnumber[0][0]

            # send back to page with title, invitees listed so far
            return render_template("new.html", inviteesnumber=inviteesnumber, message=message, user=user, status=status, reunion_id=reunion_id, title=title, invitees=invitees)

        elif 'finish_invitees' in request.form:
            """ READY ADDING INVITEES - SHOW CALENDAR """
            # save invitee to db.invitee and db.user
            status = "invited"
            reunion_id = request.form.get("reunion_id")

            # change status db.reunions to "readyaddinginvitees"
            query = 'UPDATE reunions SET status = ? WHERE id = ?'
            cursor.execute(query, ("readyaddinginvitees", reunion_id))
            connection.commit()

            # get title
            query = "SELECT title FROM reunions WHERE id = ?"
            checkresult = cursor.execute(query, (reunion_id,)).fetchall()
            title = checkresult[0][0]

            # get invitees
            query = "SELECT email FROM invitees WHERE reunion_id = ?"
            invitees = cursor.execute(query, (reunion_id,)).fetchall()

            # get possible dates from database
            date = datetime.date.today()
            date = date.strftime("%Y-%m-%d")
            query = "SELECT date, datestring, weekday, year, month, day FROM dates WHERE date > ? ORDER BY date LIMIT 60"
            result = cursor.execute(query, (date,)).fetchall()

            # send back to page with title, invitees and calender dates so far
            return render_template("new.html", message=message, user=user, status=status, reunion_id=reunion_id, title=title, invitees=invitees, result=result, inviteesnumber=inviteesnumber)

        elif 'pickdates' in request.form:
            """" DATES HAVE BEEN CHOSEN - SHOW SUMMARY """
            status = "dates_picked"
            reunion_id = request.form.get("reunion_id")

            # FIND DATESUGGESTIONS CHOSEN BY ORGANISER, FOR SAFETY REASONS SEARCH FOR DATES GIVEN BACK BY DB ONLY

            # get all possible dates from database
            date = datetime.date.today()
            date = date.strftime("%Y-%m-%d")
            query = "SELECT date FROM dates WHERE date > ? ORDER BY date LIMIT 60"
            result = cursor.execute(query, (date,)).fetchall()

            # gather all checked dates in array
            datesupload = []
            suggesteddates = []
            for checkbox in result:
                value = request.form.get(checkbox[0])
                if value:
                    suggestionsinfo = (reunion_id, checkbox[0])
                    datesupload.append(suggestionsinfo)
                    suggesteddates.append(checkbox[0])

            # insert datesuggestions in database.datesuggestions
            cursor.executemany("INSERT INTO datesuggestions (reunion_id, date) VALUES (?,?)", datesupload)
            connection.commit()

            # update status db.reunion to "readydatesuggestions"
            query = 'UPDATE reunions SET status = ? WHERE id == ?'
            cursor.execute(query, ("readydatesuggestions", reunion_id))
            connection.commit()

            # get title
            query = "SELECT title FROM reunions WHERE id = ?"
            checkresult = cursor.execute(query, (reunion_id,)).fetchall()
            title = checkresult[0][0]

            # get invitees
            query = "SELECT email FROM invitees WHERE reunion_id = ?"
            invitees = cursor.execute(query, (reunion_id,)).fetchall()

            # send to page with title, invitees, chosen dates so far
            return render_template("new.html", message=message, user=user, status=status, reunion_id=reunion_id, title=title, invitees=invitees, suggesteddates=suggesteddates)

        elif 'sendinvitations' in request.form:
            """" READY CHECKING REUNION INFO - SEND INVITATIONS """

            status = "invitationssent"
            reunion_id = request.form.get("reunion_id")
            result = ""

            # TODO: send email

            # update status db.invitees areinvited
            query = 'UPDATE invitees SET status = ? WHERE reunion_id == ?'
            cursor.execute(query, ("areinvited", reunion_id,))
            connection.commit()

            # update status db.reunions to areinvited
            query = 'UPDATE reunions SET status = ? WHERE id == ?'
            cursor.execute(query, ("areinvited", reunion_id,))
            connection.commit()

            # get title
            query = "SELECT title FROM reunions WHERE id = ?"
            checkresult = cursor.execute(query, (reunion_id,)).fetchall()
            title = checkresult[0][0]

            # get invitees
            query = "SELECT email FROM invitees WHERE reunion_id = ?"
            invitees = cursor.execute(query, (reunion_id,)).fetchall()

            # get suggested dates
            query = "SELECT date FROM datesuggestions WHERE reunion_id = ?"
            suggesteddates = cursor.execute(query, (reunion_id,)).fetchall()

            # send back to page with title, invitees, chosen dates so far to confirm invitations sent
            return render_template("new.html", message=message, user=user, status=status, reunion_id=reunion_id, title=title, invitees=invitees, suggesteddates=suggesteddates)

        return render_template("new.html", user=user, result=result)


@app.route("/availability/<reunion_id>", methods=["GET", "POST"])
def add_avail(reunion_id):
    """ SHOW PAGE TO FILL IN AVAILABILITY """
    user = session.get("user_id")

    # Make sure user is logged in
    if user is None:
        return redirect("/login")

    if request.method == "GET":
        """ SHOW PAGE TO HAVE AVAILABILITY FILLED IN """
        # get suggested dates
        query = """SELECT datesuggestions.date, dates.weekday, dates.datestring
                FROM datesuggestions
                JOIN dates ON datesuggestions.date == dates.date
                WHERE datesuggestions.reunion_id == ?"""
        suggesteddatesinfo = cursor.execute(query, (reunion_id,)).fetchall()

        # get other reunion info
        query = "SELECT title, organiser, status FROM reunions WHERE id = ?"
        reunioninfo = cursor.execute(query, (reunion_id,)).fetchall()

        # check if website user is indeed an invitee
        query = "SELECT email FROM invitees WHERE reunion_id = ? AND email = ?"
        userisinvited = cursor.execute(query, (reunion_id, user,)).fetchall()

        # TODO: make sure availability was not already been given, if so state below (and make if statement on availability.html)

        return render_template("availability.html", user=user, reunion_id=reunion_id, userisinvited=userisinvited, suggesteddatesinfo=suggesteddatesinfo, reunioninfo=reunioninfo)

    if request.method == "POST":
        """ AVAILABILITY FILLED IN - WRITE TO DATABASE """
        status = "readyavailability"

        # get suggesteddates
        query = "SELECT date FROM datesuggestions WHERE reunion_id = ?"
        datearray = cursor.execute(query, (reunion_id,)).fetchall()
        availability_upload = []

        # get user values for given suggested dates and build array to write to database availabilities
        for date in datearray:
            availability = request.form.get(date[0])
            availrow = (reunion_id, user, date[0], availability)
            availability_upload.append(availrow)

        # write availability to database
        cursor.executemany("INSERT INTO availabilities (reunion_id, email, date, status) VALUES (?,?,?,?)", availability_upload)
        connection.commit()

        # change status db.invitees
        query = 'UPDATE invitees SET status = ? WHERE reunion_id = ? and email = ?'
        cursor.execute(query, ("readyavailability", reunion_id, user,))
        connection.commit()

        # TODO: check status all invitees, if all readyavailability change status reunions

        # redirect to reunion page
        return redirect("/reunion/" + reunion_id)


@app.route("/reunion/<reunion_id>", methods=["GET", "POST"])
def reunion(reunion_id):
    """ REUNION OVERVIEW PAGE WITH AVAILABILITIES """

    # print(reunion_id)
    user = session.get("user_id")

    # make sure user is logged in
    if user is None:
        return redirect("/login")

    # get reunion info
    query = "SELECT title, organiser, status, planned_date FROM reunions WHERE id = ?"
    reunioninfo = cursor.execute(query, (reunion_id,)).fetchall()

    # check if is organiser
    query = "SELECT organiser FROM reunions WHERE id = ? AND organiser = ?"
    userisorganiser = cursor.execute(query, (reunion_id, user,)).fetchall()

    # check if is invitee
    query = "SELECT email FROM invitees WHERE reunion_id = ? AND email = ?"
    userisinvited = cursor.execute(query, (reunion_id, user,)).fetchall()

    # get availabilties
    availabilities = []
    query = "SELECT date FROM datesuggestions WHERE reunion_id = ?"
    datearray = cursor.execute(query, (reunion_id,)).fetchall()

    for adate in datearray:
        daterow = []
        daterow.append(adate[0])
        dateavails = []

        # get invitees
        query = "SELECT email,status FROM invitees WHERE reunion_id = ?"
        inviteearray = cursor.execute(query, (reunion_id,)).fetchall()

        # per invitee get status, get availability info
        for invitee in inviteearray:
            personavail = [invitee[0], invitee[1]]
            if invitee[1] == 'readyavailability':
                query = "SELECT status FROM availabilities WHERE reunion_id = ? AND email = ? AND date = ?"
                avail = cursor.execute(query, (reunion_id, invitee[0], adate[0])).fetchall()
                personavail.append(avail[0][0])
            else:
                personavail.append("awaiting")
            dateavails.append(personavail)

        daterow.append(dateavails)
        availabilities.append(daterow)

    if request.method == "GET":
        """ SHOW OVERVIEW """
        # show page
        justscheduled = False
        return render_template("reunion.html", justscheduled=justscheduled, user=user, reunion_id=reunion_id, reunioninfo=reunioninfo, userisorganiser=userisorganiser, userisinvited=userisinvited, availabilities=availabilities)

    if request.method == "POST":
        """ ORGANISER SCHEDULED A DATE (SAVE IT) - SHOW OVERVIEW """
        # get date to be scheduled and write to db
        pickeddate = request.form.get("pickeddate")
        if pickeddate:
            query = 'UPDATE reunions SET status = ?, planned_date = ? WHERE id == ?'
            cursor.execute(query, ("scheduled", pickeddate, reunion_id))
            connection.commit()

        # show page again
        justscheduled = True
        return render_template("reunion.html", justscheduled=justscheduled, pickeddate=pickeddate, user=user, reunion_id=reunion_id, reunioninfo=reunioninfo, userisorganiser=userisorganiser, userisinvited=userisinvited, availabilities=availabilities)
