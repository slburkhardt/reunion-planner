import sqlite3
import datetime

connection = sqlite3.connect("reunionplanner.db")
cursor = connection.cursor()


def checkTableExist(tablename):
    query = "SELECT name FROM sqlite_master WHERE type='table'AND name= '" + tablename + "'"
    #print (query)
    checkresult = cursor.execute(query).fetchall()
    if checkresult == []:
        # return False
        createTable(tablename)
    else:
        print("{} exist".format(tablename))


def createTable(tablename):
    print("{} doesnot exist, making {}...".format(tablename, tablename))
    if tablename == 'users':
        query = """CREATE TABLE IF NOT EXISTS users (
                	id INTEGER PRIMARY KEY,
                	first_name TEXT,
                	last_name TEXT,
                	email TEXT NOT NULL UNIQUE,
                	status TEXT NOT NULL,
                	hashkey TEXT
                    );"""
    elif tablename == 'dates':
        query = """CREATE TABLE IF NOT EXISTS dates (
                	id INTEGER PRIMARY KEY,
                	date TEXT NOT NULL UNIQUE,
                	datestring TEXT NOT NULL UNIQUE,
                	weekday TEXT NOT NULL,
                	year INTEGER NOT NULL,
                	month INTEGER NOT NULL,
                	day INTEGER NOT NULL

                    );"""
    elif tablename == 'reunions':
        query = """CREATE TABLE IF NOT EXISTS reunions (
                	id INTEGER PRIMARY KEY,
                	title TEXT NOT NULL,
                	organiser TEXT NOT NULL,
                	status TEXT NOT NULL,
                	planned_date TEXT
                    );"""
    elif tablename == 'invitees':
        query = """CREATE TABLE IF NOT EXISTS invitees (
                	id INTEGER PRIMARY KEY,
                	reunion_id TEXT NOT NULL,
                	email TEXT NOT NULL,
                	status TEXT NOT NULL
                    );"""
    elif tablename == 'datesuggestions':
        query = """CREATE TABLE IF NOT EXISTS datesuggestions (
                	id INTEGER PRIMARY KEY,
                	reunion_id TEXT NOT NULL,
                	date TEXT NOT NULL
                    );"""
    elif tablename == 'availabilities':
        query = """CREATE TABLE IF NOT EXISTS availabilities (
                	id INTEGER PRIMARY KEY,
                	reunion_id TEXT NOT NULL,
                	email TEXT NOT NULL,
                	date TEXT NOT NULL,
                	status TEXT NOT NULL
                    );"""
    created = cursor.execute(query)
    # print(query)
    print("table {} has been made by following query:{} result is {}.".format(tablename, query, created))
    if tablename == 'dates':
        print("going to populate dates (via createTable)")
        populateTable(tablename)


def populateTable(tablename):
    # (pre)filling some tables
    if tablename == 'dates':
        print("starting populateTable function")
        # check as from which date to start extending
        lastDate = cursor.execute("SELECT date,year,month,day FROM dates ORDER BY date DESC LIMIT 1").fetchall()
        day_delta = datetime.timedelta(days=1)
        # print(lastDate)
        if lastDate == []:
            start_date = datetime.date.today()
        else:
            year = lastDate[0][1]
            month = lastDate[0][2]
            day = lastDate[0][3]
            start_date = datetime.date(year, month, day) + datetime.timedelta(days=1)
            futuredays = (start_date - datetime.date.today())/day_delta
            print(futuredays)
            if futuredays > 390:
                return False
            #print((start_date - datetime.date.today())/day_delta)

        # The size of each step in days, extending 30 days
        #day_delta = datetime.timedelta(days=1)
        end_date = start_date + 30*day_delta
        print("starting gathering all info to populateTable function")
        # Gathering all date info
        dateinsert = []
        for i in range((end_date - start_date).days):
            date = (start_date + i*day_delta).strftime("%Y-%m-%d")
            weekday = (start_date + i*day_delta).strftime("%A")
            datestring = (start_date + i*day_delta).strftime("%d-%m-%Y")
            year = (start_date + i*day_delta).year
            month = (start_date + i*day_delta).month
            day = (start_date + i*day_delta).day
            dateinfo = (date, datestring, weekday, year, month, day)
            dateinsert.append(dateinfo)

        # Insert all date info into table
        cursor.executemany("INSERT INTO dates (date, datestring, weekday, year, month, day) VALUES (?,?,?,?,?,?)", dateinsert)
        connection.commit()
        print("dates has been populated with 30 extra data")