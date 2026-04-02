# I import Flask so I can create a website
# I also import render_template so I can send HTML files to the browser
from flask import Flask, render_template

# I import sqlite3 to work with a database
import sqlite3

# Here I create my web application
# __name__ just tells Flask the name of this file
app = Flask(__name__)

# This function sets up the database when the app starts
def init_db():
    # Connect to the database file
    # If the file doesn't exist, sqlite3 creates it automatically
    conn = sqlite3.connect("internships.db")
    
    # Cursor lets us send SQL commands to the database
    cursor = conn.cursor()

    # Create the scholarships table if it doesn't exist yet
    # Each line inside is a column in the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- unique number for each row, auto generated
            title TEXT NOT NULL,                   -- name of the scholarship
            university TEXT NOT NULL,              -- which university offers it
            country TEXT NOT NULL,                 -- which country it's in
            field TEXT NOT NULL,                   -- what subject area (CS, medicine, etc)
            deadline DATE NOT NULL,                -- last day to apply
            is_free INTEGER NOT NULL,              -- 1 = free to apply, 0 = has fees
            requirements TEXT,                     -- what you need to apply
            link TEXT                              -- official application link
        )
    """)

    # Check how many rows are already in the table
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
# This makes sure the database and table are always ready
init_db()

# This route handles the homepage
# When someone visits "/" (the main URL), run the function below
@app.route("/")
def home():
    # Open a connection to the database
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Fetch ALL columns we need — requirements (s[6]) and link (s[7]) are new
    cursor.execute("SELECT title, university, country, field, deadline, is_free, requirements, link FROM scholarships")
    # Store all the results in a variable
    # Each result is a tuple, like: ("CS Scholarship", "Univ of Paris", "France", ...)
    scholarships = cursor.fetchall()

    # Close the connection
    conn.close()

    # Send the data to the HTML template
    # The template can now use the variable "scholarships"
    return render_template("index.html", scholarships=scholarships)

# This route is just for debugging
# Visit /show_db in the browser to see the raw database content
@app.route("/show_db")
def show_db():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    # Get everything from the table
    cursor.execute("SELECT * FROM scholarships")
    data = cursor.fetchall()
    conn.close()

    # Show it as plain text in the browser so we can read it easily
    return "<pre>" + str(data) + "</pre>"

# This block only runs if we start the app directly with: python app.py
if __name__ == "__main__":
    # debug=True shows us helpful error messages while we're developing
    app.run(debug=True)