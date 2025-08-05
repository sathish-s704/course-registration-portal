import sqlite3
import os

# Remove existing database file if it exists
if os.path.exists("portal.db"):
    os.remove("portal.db")
    print("🗑️ Removed corrupted database file.")

try:
    # Create new database connection
    conn = sqlite3.connect("portal.db")
    cur = conn.cursor()
    
    print("🔧 Creating database tables...")
    
    # Create students table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        rollno TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)
    print("✅ Students table created")
    
    # Create courses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL
    )
    """)
    print("✅ Courses table created")
    
    # Create registrations table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        rollno TEXT,
        course_id TEXT,
        PRIMARY KEY (rollno, course_id),
        FOREIGN KEY (rollno) REFERENCES students(rollno),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )
    """)
    print("✅ Registrations table created")
    
    # Add some sample courses
    sample_courses = [
        ('CS101', 'Introduction to Computer Science'),
        ('CS102', 'Data Structures and Algorithms'),
        ('CS103', 'Database Management Systems'),
        ('CS104', 'Web Development'),
        ('CS105', 'Software Engineering')
    ]
    
    for course_id, course_name in sample_courses:
        try:
            cur.execute('INSERT INTO courses (course_id, course_name) VALUES (?, ?)', (course_id, course_name))
        except sqlite3.IntegrityError:
            print(f"⚠️ Course {course_id} already exists")
    
    print("✅ Sample courses added")
    
    conn.commit()
    conn.close()
    
    print("🎉 Database initialized successfully!")
    print("📊 Database file size:", os.path.getsize("portal.db"), "bytes")
    
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    if os.path.exists("portal.db"):
        os.remove("portal.db")
        print("🗑️ Removed corrupted database file.")
