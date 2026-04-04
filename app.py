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

    # Check how many rows are already in the scholarships table
    # We do this to avoid inserting duplicate data every time the server restarts
    cursor.execute("SELECT COUNT(*) FROM scholarships")
    count = cursor.fetchone()[0]  # fetchone() gets one result, [0] gets the number from it

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
    query = "SELECT title, university, country, field, deadline, is_free, requirements, link FROM scholarships WHERE 1=1"

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

    # Show it as plain text in the browser so we can read it easily
    return "<pre>" + str(data) + "</pre>"

# This route SHOWS the signup page
# When someone visits /signup in their browser, they see the form
@app.route("/signup")
def signup():
    return render_template("signup.html")

# This route HANDLES the signup form when it's submitted
# "POST" means this only runs when the form is submitted, not just visited
@app.route("/signup", methods=["POST"])
def signup_post():
    # Read the email and password the user typed in the form
    email = request.form.get("email")
    password = request.form.get("password")

    # Connect to the database to check if email already exists
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Look for a user with this exact email
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()  # returns None if no user found

    # If a user with this email already exists, tell them
    if existing_user:
        conn.close()
        # Send them back to signup page with a friendly message
        return render_template("signup.html", message="This email is already registered! Did you mean to log in?")

    # If we get here, email is new — safe to create the account!
    # Scramble the password into a hash so we never store it as plain text
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Save the new user in the database
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
    conn.commit()
    conn.close()

    # Account created! Send them to the login page
    return redirect(url_for("home"))

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

    # Show it as plain text in the browser
    return "<pre>" + str(data) + "</pre>"
# This route SHOWS the login page
# When someone visits /login in their browser, they see the form
@app.route("/login")
def login():
    return render_template("login.html")


# This route HANDLES the login form when it's submitted
@app.route("/login", methods=["POST"])
def login_post():
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

    # If we get here, everything is correct!
    # Save the user's id in the session so Flask remembers them
    # user[0] is the id column from the database
    session["user_id"] = user[0]

    # Send them to the homepage — they are now logged in!
    return redirect(url_for("home"))



# This block only runs if we start the app directly with: python app.py
if __name__ == "__main__":
    # debug=True shows us helpful error messages while we're developing
    app.run(debug=True)