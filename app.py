from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_db_connection():
    try:
        conn = sqlite3.connect('portal.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        # If database is corrupted, try to recreate it
        if os.path.exists('portal.db'):
            os.remove('portal.db')
            print("Removed corrupted database, please run init_db.py to recreate it.")
        raise e

def ensure_database_exists():
    """Ensure database exists and has proper structure"""
    if not os.path.exists('portal.db'):
        print("Database not found. Please run init_db.py to initialize the database.")
        return False
    
    try:
        conn = get_db_connection()
        # Test if database is valid by checking if tables exist
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
        conn.close()
        return True
    except sqlite3.DatabaseError:
        print("Database is corrupted. Please run init_db.py to recreate it.")
        return False

@app.route('/')
def index():
    return render_template('index.html')

# ---------- Admin Routes ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == 'admin123':
            session['admin'] = True
            flash('🎉 Welcome! Admin login successful.')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('❌ Invalid admin password. Please try again.')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('add_course.html')
    
    if request.method == 'POST':
        course_id = request.form['course_id']
        course_name = request.form['course_name']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO courses (course_id, course_name) VALUES (?, ?)', (course_id, course_name))
            conn.commit()
            flash(f"✅ Course '{course_name}' (ID: {course_id}) added successfully!")
        except sqlite3.IntegrityError:
            flash(f"⚠️ Course ID '{course_id}' already exists. Please use a different ID.")
        except Exception as e:
            flash(f"❌ Error adding course: {str(e)}")
        finally:
            conn.close()
    return render_template('add_course.html')

@app.route('/admin/courses')
def view_courses():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('view_course.html', courses=[])
    
    try:
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses').fetchall()
        conn.close()
        if not courses:
            flash("📝 No courses available. Add some courses to get started!")
        return render_template('view_course.html', courses=courses)
    except Exception as e:
        flash(f"❌ Error loading courses: {str(e)}")
        return render_template('view_course.html', courses=[])

@app.route('/admin/delete_course/<course_id>')
def delete_course(course_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return redirect(url_for('view_courses'))
    
    try:
        conn = get_db_connection()
        # Get course name before deleting
        course = conn.execute('SELECT course_name FROM courses WHERE course_id = ?', (course_id,)).fetchone()
        course_name = course['course_name'] if course else course_id
        
        conn.execute('DELETE FROM courses WHERE course_id = ?', (course_id,))
        conn.commit()
        conn.close()
        flash(f"🗑️ Course '{course_name}' (ID: {course_id}) deleted successfully!")
    except Exception as e:
        flash(f"❌ Error deleting course: {str(e)}")
    return redirect(url_for('view_courses'))

@app.route('/admin/registered_students')
def view_registered_students():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('registered_students.html', students=[])
    
    try:
        conn = get_db_connection()
        # Get all students with their registered courses
        students_data = conn.execute('''
            SELECT DISTINCT s.rollno, s.name, 
                   GROUP_CONCAT(c.course_name, ', ') as registered_courses,
                   COUNT(r.course_id) as course_count
            FROM students s
            LEFT JOIN registrations r ON s.rollno = r.rollno
            LEFT JOIN courses c ON r.course_id = c.course_id
            GROUP BY s.rollno, s.name
            ORDER BY s.name
        ''').fetchall()
        conn.close()
        
        if not students_data:
            flash("📝 No students registered yet. Students will appear here once they register for courses.")
        else:
            flash(f"👥 Found {len(students_data)} registered student(s).")
            
        return render_template('registered_students.html', students=students_data)
    except Exception as e:
        flash(f"❌ Error loading registered students: {str(e)}")
        return render_template('registered_students.html', students=[])

# ---------- Student Routes ----------
@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('student_register.html')
    
    if request.method == 'POST':
        rollno = request.form['rollno']
        name = request.form['name']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO students (rollno, name, password) VALUES (?, ?, ?)', (rollno, name, password))
            conn.commit()
            flash(f"🎉 Registration successful! Welcome {name}! Please login with your credentials.")
            conn.close()
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash(f"⚠️ Roll number '{rollno}' already registered. Please use a different roll number.")
        except Exception as e:
            flash(f"❌ Error during registration: {str(e)}")
        finally:
            conn.close()
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('student_login.html')
    
    if request.method == 'POST':
        rollno = request.form['rollno']
        password = request.form['password']
        conn = get_db_connection()
        try:
            student = conn.execute('SELECT * FROM students WHERE rollno = ? AND password = ?', (rollno, password)).fetchone()
            if student:
                session['student'] = rollno
                flash(f"🎉 Welcome back, {student['name']}! Login successful.")
                return redirect(url_for('student_dashboard'))
            else:
                flash("❌ Invalid credentials. Please check your roll number and password.")
        except Exception as e:
            flash(f"❌ Error during login: {str(e)}")
        finally:
            conn.close()
    return render_template('student_login.html')

@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'student' not in session:
        return redirect(url_for('student_login'))

    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('student_dashboard.html', courses=[], registered=set())

    try:
        conn = get_db_connection()
        rollno = session['student']
        courses = conn.execute('SELECT * FROM courses').fetchall()
        registered = conn.execute('SELECT course_id FROM registrations WHERE rollno = ?', (rollno,)).fetchall()
        registered_ids = {r['course_id'] for r in registered}

        if request.method == 'POST':
            selected = request.form.getlist('courses')
            if selected:
                new_registrations = 0
                for cid in selected:
                    if cid not in registered_ids:
                        conn.execute('INSERT INTO registrations (rollno, course_id) VALUES (?, ?)', (rollno, cid))
                        new_registrations += 1
                
                if new_registrations > 0:
                    conn.commit()
                    flash(f"✅ Successfully registered for {new_registrations} new course(s)!")
                else:
                    flash("ℹ️ No new courses selected for registration.")
            else:
                flash("ℹ️ Please select at least one course to register.")
        conn.close()

        return render_template('student_dashboard.html', courses=courses, registered=registered_ids)
    except Exception as e:
        flash(f"❌ Error loading dashboard: {str(e)}")
        return render_template('student_dashboard.html', courses=[], registered=set())

@app.route('/student/my_courses')
def my_registered_courses():
    if 'student' not in session:
        return redirect(url_for('student_login'))

    if not ensure_database_exists():
        flash("❌ Database error. Please contact administrator.")
        return render_template('my_courses.html', courses=[])

    try:
        conn = get_db_connection()
        rollno = session['student']
        
        # Get student's registered courses with course details
        registered_courses = conn.execute('''
            SELECT c.course_id, c.course_name, r.rollno
            FROM registrations r
            JOIN courses c ON r.course_id = c.course_id
            WHERE r.rollno = ?
            ORDER BY c.course_name
        ''', (rollno,)).fetchall()
        
        # Get student info
        student_info = conn.execute('SELECT name FROM students WHERE rollno = ?', (rollno,)).fetchone()
        conn.close()
        
        if not registered_courses:
            flash("📝 You haven't registered for any courses yet. Visit the dashboard to register for courses!")
        else:
            flash(f"📚 You are registered for {len(registered_courses)} course(s).")
        
        return render_template('my_courses.html', courses=registered_courses, student_info=student_info)
    except Exception as e:
        flash(f"❌ Error loading your courses: {str(e)}")
        return render_template('my_courses.html', courses=[])

@app.route('/logout')
def logout():
    if session.get('admin'):
        flash("👋 Admin logged out successfully.")
    elif session.get('student'):
        flash("👋 Logged out successfully. Come back soon!")
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
