# I import Flask so I can create a website
from flask import Flask, render_template, request, session, redirect, url_for

# To scramble passwords we need bcrypt
from flask_bcrypt import Bcrypt

# I import sqlite3 to work with a database
import sqlite3

# Here I create my web application
app = Flask(__name__)

# Secret key for sessions — keeps cookies secure
app.secret_key = "mysecretkey123"

# Fixes cookie issues in development
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

# Connects bcrypt to our app so we can hash passwords
bcrypt = Bcrypt(app)

# Your email — only this email can access the admin page
ADMIN_EMAIL = "chahinezouar02@gmail.com"


# =============================================
# DATABASE SETUP
# Creates all tables when the app starts.
# No fake data anymore — use the admin page to add real scholarships!
# =============================================
def init_db():
    # Connect to the database file
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Scholarships table
    # Stores all the scholarships displayed on the homepage
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

    # Users table
    # Stores everyone who signs up
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    # Saved scholarships table
    # Connects users to scholarships they saved to their list
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scholarship_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reviews table
    # Stores ratings and comments left by users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scholarship_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# Run init_db once when the app starts
init_db()


# =============================================
# HOMEPAGE
# =============================================
@app.route("/")
def home():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Read filter choices from the URL
    country = request.args.get("country", "")
    field = request.args.get("field", "")
    is_free = request.args.get("is_free", "")

    # Base query — fetches everything
    query = "SELECT id, title, university, country, field, deadline, is_free, requirements, link FROM scholarships WHERE 1=1"
    params = []

    # Add filters if the user picked any
    if country:
        query += " AND country = ?"
        params.append(country)
    if field:
        query += " AND field = ?"
        params.append(field)
    if is_free:
        query += " AND is_free = 1"

    cursor.execute(query, params)
    scholarships = cursor.fetchall()
    conn.close()

    return render_template("index.html", scholarships=scholarships)


# =============================================
# AUTHENTICATION — SIGNUP, LOGIN, LOGOUT
# =============================================

# Shows and handles the signup form
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template("signup.html", message="This email is already registered! Did you mean to log in?")

        # Hash the password and save the user
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# Shows and handles the login form
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return render_template("login.html", message="No account found with this email!")

        # Check if the password matches the hash
        password_matches = bcrypt.check_password_hash(user[2], password)

        if not password_matches:
            return render_template("login.html", message="Wrong password, try again!")

        # Save user id in session — this keeps them logged in
        session["user_id"] = user[0]

        return redirect(url_for("home"))

    return render_template("login.html")


# Logs the user out by clearing the session
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


# =============================================
# SAVE & MY LIST
# =============================================

# Saves a scholarship to the user's personal list
@app.route("/save/<int:scholarship_id>")
def save_scholarship(scholarship_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Only save if not already saved
    cursor.execute("""
        SELECT * FROM saved_scholarships
        WHERE user_id = ? AND scholarship_id = ?
    """, (user_id, scholarship_id))
    already_saved = cursor.fetchone()

    if not already_saved:
        cursor.execute("""
            INSERT INTO saved_scholarships (user_id, scholarship_id)
            VALUES (?, ?)
        """, (user_id, scholarship_id))
        conn.commit()

    conn.close()
    return redirect(url_for("home"))


# Shows the user's saved scholarships
@app.route("/my-list")
def my_list():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # JOIN connects saved_scholarships with scholarships
    # to get the full details of each saved scholarship
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

    return render_template("my_list.html", scholarships=scholarships)


# Removes a scholarship from the user's saved list
@app.route("/remove/<int:scholarship_id>")
def remove_scholarship(scholarship_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM saved_scholarships
        WHERE user_id = ? AND scholarship_id = ?
    """, (user_id, scholarship_id))

    conn.commit()
    conn.close()
    return redirect(url_for("my_list"))


# =============================================
# SCHOLARSHIP DETAIL PAGE & REVIEWS
# =============================================

# Shows the full detail page for one scholarship
@app.route("/scholarship/<int:scholarship_id>")
def scholarship_detail(scholarship_id):
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Fetch the scholarship
    cursor.execute("""
        SELECT id, title, university, country, field,
               deadline, is_free, requirements, link
        FROM scholarships WHERE id = ?
    """, (scholarship_id,))
    scholarship = cursor.fetchone()

    # Fetch all reviews for this scholarship
    cursor.execute("""
        SELECT r.rating, r.comment, r.created_at, u.email
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.scholarship_id = ?
        ORDER BY r.created_at DESC
    """, (scholarship_id,))
    reviews = cursor.fetchall()

    # Calculate average rating
    cursor.execute("SELECT AVG(rating) FROM reviews WHERE scholarship_id = ?", (scholarship_id,))
    avg = cursor.fetchone()[0]
    average_rating = round(avg, 1) if avg else 0

    conn.close()

    return render_template("scholarship_detail.html",
        scholarship=scholarship,
        reviews=reviews,
        average_rating=average_rating
    )


# Handles submitting a review
@app.route("/review/<int:scholarship_id>", methods=["POST"])
def submit_review(scholarship_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    rating = request.form.get("rating")
    comment = request.form.get("comment")

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # One review per user per scholarship
    cursor.execute("""
        SELECT * FROM reviews
        WHERE user_id = ? AND scholarship_id = ?
    """, (user_id, scholarship_id))
    already_reviewed = cursor.fetchone()

    if not already_reviewed:
        cursor.execute("""
            INSERT INTO reviews (user_id, scholarship_id, rating, comment)
            VALUES (?, ?, ?, ?)
        """, (user_id, scholarship_id, rating, comment))
        conn.commit()

    conn.close()
    return redirect(url_for("scholarship_detail", scholarship_id=scholarship_id))


# =============================================
# ADMIN PAGE
# Only accessible by the admin email
# =============================================

# Shows the admin panel
@app.route("/admin")
def admin():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    if not user or user[0] != ADMIN_EMAIL:
        conn.close()
        return "<h1>Access Denied</h1><p>You are not allowed to view this page.</p>", 403

    cursor.execute("SELECT id, title, university, country, deadline FROM scholarships")
    scholarships = cursor.fetchall()
    conn.close()

    return render_template("admin.html", scholarships=scholarships)


# Handles adding a new scholarship from the admin form
@app.route("/admin/add", methods=["POST"])
def admin_add():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    if not user or user[0] != ADMIN_EMAIL:
        conn.close()
        return "<h1>Access Denied</h1>", 403

    # Read all form fields
    title = request.form.get("title")
    university = request.form.get("university")
    country = request.form.get("country")
    field = request.form.get("field")
    deadline = request.form.get("deadline")
    is_free = int(request.form.get("is_free"))
    requirements = request.form.get("requirements")
    link = request.form.get("link")

    cursor.execute("""
        INSERT INTO scholarships
        (title, university, country, field, deadline, is_free, requirements, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, university, country, field, deadline, is_free, requirements, link))

    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


# Handles deleting a scholarship from the admin panel
@app.route("/admin/delete/<int:scholarship_id>")
def admin_delete(scholarship_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()

    if not user or user[0] != ADMIN_EMAIL:
        conn.close()
        return "<h1>Access Denied</h1>", 403

    cursor.execute("DELETE FROM scholarships WHERE id = ?", (scholarship_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


# =============================================
# START THE APP
# =============================================
if __name__ == "__main__":
    app.run(debug=True, host="localhost")
    