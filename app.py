# I import Flask so I can create a website
# I also import render_template so I can send HTML files to the browser
from flask import Flask, render_template, request, session, redirect, url_for

# To scramble passwords we need bcrypt
from flask_bcrypt import Bcrypt

# I import sqlite3 to work with a database
import sqlite3

# Here I create my web application
# __name__ just tells Flask the name of this file
app = Flask(__name__)

# This is needed for sessions to work
# It's a secret key Flask uses to protect the cookie
# Think of it as a password that only your server knows
app.secret_key = "mysecretkey123"

# This fixes cookie issues in development
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

# This connects bcrypt to our app so we can hash passwords
bcrypt = Bcrypt(app)

# This function sets up the database when the app starts
def init_db():
    # Connect to the database file
    # If the file doesn't exist, sqlite3 creates it automatically
    conn = sqlite3.connect("internships.db")

    # Cursor lets us send SQL commands to the database
    cursor = conn.cursor()

    # Create the scholarships table if it doesn't exist yet
    # id = unique number for each row, auto generated
    # title = name of the scholarship
    # university = which university offers it
    # country = which country it's in
    # field = what subject area (CS, medicine, etc)
    # deadline = last day to apply
    # is_free = 1 means free to apply, 0 means has fees
    # requirements = what you need to apply
    # link = official application link
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            university TEXT NOT NULL,
            country TEXT NOT NULL,
            field TEXT NOT NULL,
            deadline DATE NOT NULL,
            is_free INTEGER NOT NULL,
            requirements TEXT,
            link TEXT
        )
    """)

    # Create the users table if it doesn't exist yet
    # id = unique number for each user
    # email = must be unique, no two users can have the same email
    # password = stores the hashed (scrambled) password, never plain text
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    
    # Create the saved_scholarships table
# This connects users to scholarships they want to track
# user_id = which user saved it
# scholarship_id = which scholarship they saved
# saved_at = when they saved it (automatically set to now)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scholarship_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
    
    
    
    
    
    
    
    
    
    

    # Check how many rows are already in the scholarships table
    # We do this to avoid inserting duplicate data every time the server restarts
    cursor.execute("SELECT COUNT(*) FROM scholarships")
    count = cursor.fetchone()[0]

    # Only insert fake test data if the table is completely empty
    if count == 0:

        # First fake scholarship
        cursor.execute("""
            INSERT INTO scholarships 
            (title, university, country, field, deadline, is_free, requirements, link)
            VALUES (
                'Computer Science Scholarship',
                'University of Paris',
                'France',
                'Computer Science',
                '2025-06-01',
                1,
                'Bachelor degree, GPA above 3.0, motivation letter',
                'https://example.com/apply'
            )
        """)

        # Second fake scholarship
        cursor.execute("""
            INSERT INTO scholarships 
            (title, university, country, field, deadline, is_free, requirements, link)
            VALUES (
                'AI Research Grant',
                'Berlin Tech University',
                'Germany',
                'Artificial Intelligence',
                '2025-07-15',
                1,
                'Bachelor degree, recommendation letter',
                'https://example.com/apply2'
            )
        """)

    # Save all changes to the database file
    conn.commit()

    # Close the connection, we don't need it anymore
    conn.close()

# Run init_db once when the app starts
# This makes sure the database and tables are always ready
init_db()

# This route handles the homepage
# When someone visits "/" (the main URL), run the function below
@app.route("/")
def home():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Read filter choices from the URL
    # If the user didn't pick anything, these will just be empty strings
    country = request.args.get("country", "")
    field = request.args.get("field", "")
    is_free = request.args.get("is_free", "")

    # Start with a base query that fetches everything
    query = "SELECT id, title, university, country, field, deadline, is_free, requirements, link FROM scholarships WHERE 1=1"

    # This list will hold the actual filter values
    params = []

    # If the user picked a country, add it to the query
    if country:
        query += " AND country = ?"
        params.append(country)

    # If the user picked a field, add it to the query
    if field:
        query += " AND field = ?"
        params.append(field)

    # If the user checked "free only", add it to the query
    if is_free:
        query += " AND is_free = 1"

    # Run the final query with whatever filters were added
    cursor.execute(query, params)
    scholarships = cursor.fetchall()
    conn.close()

    return render_template("index.html", scholarships=scholarships)

# This route is just for debugging
# Visit /show_db in the browser to see the raw database content
@app.route("/show_db")
def show_db():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Get everything from the scholarships table
    cursor.execute("SELECT * FROM scholarships")
    data = cursor.fetchall()
    conn.close()

    return "<pre>" + str(data) + "</pre>"

# Temporary debug route to see all registered users
# Visit /show_users in the browser to check the database
@app.route("/show_users")
def show_users():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Get all users from the users table
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    conn.close()

    return "<pre>" + str(data) + "</pre>"

# Debug route — shows what's inside the session right now
# Visit /show_session after logging in to check if session is working
@app.route("/show_session")
def show_session():
    return "<pre>" + str(dict(session)) + "</pre>"

# This route handles both SHOWING and SUBMITTING the signup form
# GET = someone visits /signup → just show the empty form
# POST = someone submitted the form → process it
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Read the email and password the user typed in the form
        email = request.form.get("email")
        password = request.form.get("password")

        # Connect to the database to check if email already exists
        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        # Look for a user with this exact email
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        # If a user with this email already exists, tell them
        if existing_user:
            conn.close()
            return render_template("signup.html", message="This email is already registered! Did you mean to log in?")

        # Email is new — scramble the password and save the user
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()

        # Account created! Send them to the login page
        return redirect(url_for("login"))

    # If just visiting /signup → show the empty form
    return render_template("signup.html")

# This route handles both SHOWING and SUBMITTING the login form
# GET = someone visits /login → just show the empty form
# POST = someone submitted the form → check email and password
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Read the email and password the user typed
        email = request.form.get("email")
        password = request.form.get("password")

        # Connect to the database
        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        # Look for a user with this email
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        # If no user found with this email, tell them
        if not user:
            return render_template("login.html", message="No account found with this email!")

        # user[2] is the hashed password stored in the database
        # bcrypt checks if the typed password matches the hash
        password_matches = bcrypt.check_password_hash(user[2], password)

        # If password is wrong, tell them
        if not password_matches:
            return render_template("login.html", message="Wrong password, try again!")

        # Everything correct! Save the user id in the session
        # This is what keeps the user logged in across pages
        session["user_id"] = user[0]
        print("SESSION AFTER LOGIN:", dict(session))  # this prints in the terminal

        # Send them to the homepage — they are now logged in!
        return redirect(url_for("home"))

    # If just visiting /login → show the empty form
    return render_template("login.html")

# This route logs the user out
# It clears the session and sends them back to the homepage
@app.route("/logout")
def logout():
    # Remove the user_id from the session
    # This is like taking off the wristband — Flask forgets who you are
    session.pop("user_id", None)

    # Send them back to the homepage
    return redirect(url_for("home"))


# This route saves a scholarship to the user's personal list
# It only works if the user is logged in
@app.route("/save/<int:scholarship_id>")
def save_scholarship(scholarship_id):

    # Check if the user is logged in
    # If not, send them to the login page
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Get the logged in user's id from the session
    user_id = session["user_id"]

    # Connect to the database
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Check if this scholarship is already saved by this user
    # We don't want duplicates in the list
    cursor.execute("""
        SELECT * FROM saved_scholarships 
        WHERE user_id = ? AND scholarship_id = ?
    """, (user_id, scholarship_id))
    already_saved = cursor.fetchone()

    # Only save it if it's not already in the list
    if not already_saved:
        cursor.execute("""
            INSERT INTO saved_scholarships (user_id, scholarship_id)
            VALUES (?, ?)
        """, (user_id, scholarship_id))
        conn.commit()

    conn.close()

    # Send them back to the homepage after saving
    return redirect(url_for("home"))

# This route shows the user's personal saved scholarships list
# Only logged in users can see this page
@app.route("/my-list")
def my_list():

    # If the user is not logged in, send them to login page
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Get the logged in user's id
    user_id = session["user_id"]

    # Connect to the database
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Fetch all scholarships that this user saved
    # We JOIN two tables together:
    # saved_scholarships (which has user_id and scholarship_id)
    # scholarships (which has all the scholarship details)
    # JOIN means: "connect rows from both tables where the ids match"
    cursor.execute("""
        SELECT s.id, s.title, s.university, s.country, s.field,
               s.deadline, s.is_free, s.requirements, s.link
        FROM scholarships s
        JOIN saved_scholarships ss ON s.id = ss.scholarship_id
        WHERE ss.user_id = ?
        ORDER BY s.deadline ASC
    """, (user_id,))

    scholarships = cursor.fetchall()
    conn.close()

    # Send the saved scholarships to the my-list page
    return render_template("my_list.html", scholarships=scholarships)

# This route removes a scholarship from the user's saved list
@app.route("/remove/<int:scholarship_id>")
def remove_scholarship(scholarship_id):

    # If not logged in, send to login
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Delete only this user's saved entry for this scholarship
    # We check both user_id AND scholarship_id so users
    # can only remove their OWN saved scholarships
    cursor.execute("""
        DELETE FROM saved_scholarships
        WHERE user_id = ? AND scholarship_id = ?
    """, (user_id, scholarship_id))

    conn.commit()
    conn.close()

    # Send them back to their list
    return redirect(url_for("my_list"))






# This block only runs if we start the app directly with: python app.py
if __name__ == "__main__":
    # debug=True shows us helpful error messages while we're developing
    app.run(debug=True, host="localhost")