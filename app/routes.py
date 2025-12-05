from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import get_db_connection
import psycopg2.extras

main = Blueprint("main", __name__)


# -----------------------------
# Home → Student List
# -----------------------------
@main.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT s.student_id, s.first_name, s.last_name, s.email,
               d.department_name, s.status
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        ORDER BY s.student_id
    """)
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", students=students)


# -----------------------------
# Student Detail
# -----------------------------
@main.route("/students/<int:student_id>")
def student_detail(student_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # student info
    cur.execute("""
        SELECT s.student_id, s.first_name, s.last_name, s.email,
               s.enrollment_year, s.gpa, s.status,
               d.department_name
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.department_id
        WHERE student_id = %s
    """, (student_id,))
    student = cur.fetchone()

    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("main.index"))

    # enrollments
    cur.execute("""
        SELECT 
            e.enrollment_id,
            c.course_code,
            c.course_name,
            sm.term,
            sm.year,
            e.status,
            e.grade
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        JOIN semesters sm ON e.semester_id = sm.semester_id
        WHERE e.student_id = %s
        ORDER BY sm.year DESC, sm.term DESC
    """, (student_id,))
    enrollments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("student_detail.html", student=student, enrollments=enrollments)


# -----------------------------
# Add Student
# -----------------------------
@main.route("/students/add", methods=["GET", "POST"])
def add_student():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        dept = request.form["department_id"]
        year = request.form["enrollment_year"]

        if not first or not last:
            flash("First and Last name are required.", "danger")
            return redirect(url_for("main.add_student"))

        # -----------------------------
        # Email duplication check
        # -----------------------------
        cur.execute(
            "SELECT student_id FROM students WHERE email = %s", (email,))
        existing_email = cur.fetchone()

        if existing_email:
            flash("Error: This email is already used by another student.", "danger")
            return redirect(url_for("main.add_student"))

        # -----------------------------
        # Insert new student
        # -----------------------------
        cur.execute("""
            INSERT INTO students (first_name, last_name, email, department_id, enrollment_year, status)
            VALUES (%s, %s, %s, %s, %s, 'Active')
        """, (first, last, email, dept, year))

        conn.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for("main.index"))

    # Load departments
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("student_add.html", departments=departments)


# -----------------------------
# Edit Student
# -----------------------------
@main.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        dept = request.form["department_id"]
        year = request.form["enrollment_year"]
        status = request.form["status"]

        cur.execute("""
            UPDATE students
            SET first_name=%s, last_name=%s, email=%s,
                department_id=%s, enrollment_year=%s, status=%s
            WHERE student_id=%s
        """, (first, last, email, dept, year, status, student_id))

        conn.commit()
        flash("Student updated successfully!", "success")
        return redirect(url_for("main.student_detail", student_id=student_id))

    # load student
    cur.execute("""
        SELECT student_id, first_name, last_name, email,
               enrollment_year, gpa, status, department_id
        FROM students
        WHERE student_id=%s
    """, (student_id,))
    student = cur.fetchone()

    # load departments
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("student_edit.html", student=student, departments=departments)


# -----------------------------
# Soft Delete Student
# -----------------------------
@main.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        UPDATE students SET status='Inactive'
        WHERE student_id=%s
    """, (student_id,))
    conn.commit()

    flash("Student deleted (soft delete).", "success")
    return redirect(url_for("main.index"))


# ==========================================================
# COURSE CRUD
# ==========================================================

# -----------------------------
# Course List
# -----------------------------
@main.route("/courses")
def course_list():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT 
            c.course_id,
            c.course_code,
            c.course_name,
            c.credits,
            c.capacity,
            (
                SELECT COUNT(*) FROM enrollments e 
                WHERE e.course_id = c.course_id AND e.status='Enrolled'
            ) AS enrolled_count
        FROM courses c
        WHERE c.status='Active'
        ORDER BY c.course_code
    """)
    courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("courses.html", courses=courses)


# -----------------------------
# Course Detail
# -----------------------------
@main.route("/courses/<int:course_id>")
def course_detail(course_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # course info
    cur.execute("""
        SELECT 
            c.course_id, c.course_code, c.course_name, 
            c.credits, c.level, c.capacity,
            d.department_name,
            i.first_name || ' ' || i.last_name AS instructor_name,
            (
                SELECT COUNT(*) FROM enrollments e 
                WHERE e.course_id = c.course_id AND e.status='Enrolled'
            ) AS enrolled_count
        FROM courses c
        JOIN departments d ON c.department_id = d.department_id
        JOIN instructors i ON c.instructor_id = i.instructor_id
        WHERE c.course_id=%s
    """, (course_id,))
    course = cur.fetchone()

    # enrolled students
    cur.execute("""
        SELECT s.student_id, 
               s.first_name || ' ' || s.last_name AS student_name,
               e.status, e.grade
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        WHERE e.course_id=%s
        ORDER BY s.student_id
    """, (course_id,))
    enrollments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("course_detail.html", course=course, enrollments=enrollments)


# -----------------------------
# Add Course
# -----------------------------
@main.route("/courses/add", methods=["GET", "POST"])
def add_course():

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        code = request.form["course_code"]
        name = request.form["course_name"]
        credits = request.form["credits"]
        level = request.form["level"]
        capacity = request.form["capacity"]
        dept = request.form["department_id"]
        inst = request.form["instructor_id"]

        cur.execute("""
            INSERT INTO courses 
                (course_code, course_name, credits, level, capacity, department_id, instructor_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (code, name, credits, level, capacity, dept, inst))

        conn.commit()
        flash("Course added successfully!", "success")
        return redirect(url_for("main.course_list"))

    # load departments
    cur.execute("SELECT * FROM departments ORDER BY department_name")
    departments = cur.fetchall()

    # load instructors
    cur.execute("""
        SELECT instructor_id, first_name, last_name 
        FROM instructors
        ORDER BY last_name
    """)
    instructors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("course_add.html", departments=departments, instructors=instructors)


# -----------------------------
# Edit Course
# -----------------------------
@main.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        code = request.form["course_code"]
        name = request.form["course_name"]
        credits = request.form["credits"]
        level = request.form["level"]
        capacity = request.form["capacity"]
        dept = request.form["department_id"]
        inst = request.form["instructor_id"]

        cur.execute("""
            UPDATE courses
            SET course_code=%s, course_name=%s, credits=%s,
                level=%s, capacity=%s, department_id=%s, instructor_id=%s
            WHERE course_id=%s
        """, (code, name, credits, level, capacity, dept, inst, course_id))

        conn.commit()
        flash("Course updated successfully!", "success")
        return redirect(url_for("main.course_detail", course_id=course_id))

    # course info
    cur.execute("SELECT * FROM courses WHERE course_id=%s", (course_id,))
    course = cur.fetchone()

    # departments
    cur.execute("SELECT * FROM departments ORDER BY department_name")
    departments = cur.fetchall()

    # instructors
    cur.execute("SELECT instructor_id, first_name, last_name FROM instructors")
    instructors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("course_edit.html", course=course, departments=departments, instructors=instructors)


# -----------------------------
# Soft Delete Course
# -----------------------------
@main.route("/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        UPDATE courses SET status='Inactive'
        WHERE course_id=%s
    """, (course_id,))
    conn.commit()

    flash("Course deleted (soft delete).", "warning")
    return redirect(url_for("main.course_list"))


# ==========================================================
# ENROLLMENT
# ==========================================================

@main.route("/students/<int:student_id>/enroll")
def enroll_page(student_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # student
    cur.execute("""
        SELECT student_id, first_name, last_name 
        FROM students
        WHERE student_id=%s
    """, (student_id,))
    student = cur.fetchone()

    # courses with enrolled count
    cur.execute("""
        SELECT 
            c.course_id,
            c.course_code,
            c.course_name,
            c.credits,
            c.capacity,
            (
                SELECT COUNT(*) FROM enrollments e 
                WHERE e.course_id = c.course_id AND e.status='Enrolled'
            ) AS enrolled_count
        FROM courses c
        WHERE c.status='Active'
        ORDER BY c.course_code
    """)
    courses = cur.fetchall()

    # semesters
    cur.execute(
        "SELECT semester_id, term, year FROM semesters ORDER BY year DESC")
    semesters = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("enroll_add.html",
                           student=student, courses=courses, semesters=semesters)


# -----------------------------
# Submit Enrollment
# -----------------------------
@main.route("/students/<int:student_id>/enroll/submit", methods=["POST"])
def enroll_submit(student_id):

    course_id = request.form["course_id"]
    semester_id = request.form["semester_id"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:

        # 1. capacity check
        cur.execute("""
            SELECT capacity,
                (SELECT COUNT(*) FROM enrollments e 
                 WHERE e.course_id=%s AND e.status='Enrolled') AS enrolled_count
            FROM courses
            WHERE course_id=%s
        """, (course_id, course_id))
        info = cur.fetchone()

        if info["enrolled_count"] >= info["capacity"]:
            raise Exception("Course is full")

        # 2. insert enrollment
        cur.execute("""
            INSERT INTO enrollments (student_id, course_id, semester_id, status)
            VALUES (%s, %s, %s, 'Enrolled')
        """, (student_id, course_id, semester_id))

        conn.commit()
        flash("Enrollment added successfully!", "success")
        return redirect(url_for("main.student_detail", student_id=student_id))

    except Exception as e:
        conn.rollback()

        error_msg = str(e)

        if "duplicate" in error_msg.lower():
            flash("Error: Student already enrolled in this course.", "danger")
        elif "full" in error_msg.lower():
            flash("Error: Course is full.", "danger")
        else:
            flash("Unexpected error occurred.", "danger")

        return redirect(url_for("main.enroll_page", student_id=student_id))

    finally:
        cur.close()
        conn.close()


# -----------------------------
# Enrollment List (GLOBAL)
# -----------------------------
@main.route("/enrollments")
def enrollment_list():

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT 
            e.enrollment_id,
            s.first_name || ' ' || s.last_name AS student_name,
            c.course_code,
            c.course_name,
            sm.term,
            sm.year,
            e.status,
            e.grade
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN courses c ON e.course_id = c.course_id
        JOIN semesters sm ON e.semester_id = sm.semester_id
        ORDER BY sm.year DESC, sm.term DESC
    """)

    enrollments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("enrollment_list.html", enrollments=enrollments)
