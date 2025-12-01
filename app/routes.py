from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .models import get_db_connection

main = Blueprint("main", __name__)

# ============================
# STUDENT LIST PAGE
# ============================


@main.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.student_id, s.first_name, s.last_name, s.email, d.department_name
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        WHERE s.status != 'Inactive'
        ORDER BY s.student_id
    """)
    students = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("index.html", students=students)


# ============================
# STUDENT DETAIL PAGE
# ============================
@main.route("/students/<int:student_id>")
def student_detail(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # --- 1. student info ---
    cur.execute("""
        SELECT 
            s.student_id, s.first_name, s.last_name, s.email,
            s.enrollment_year, s.gpa, s.status, d.department_name
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        WHERE s.student_id = %s
    """, (student_id,))
    student = cur.fetchone()

    if student is None:
        abort(404)

    # --- 2. enrollments ---
    cur.execute("""
        SELECT 
            c.course_code, c.course_name,
            sem.term, sem.year,
            e.status, e.grade
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        JOIN semesters sem ON e.semester_id = sem.semester_id
        WHERE e.student_id = %s
        ORDER BY sem.year, sem.term, c.course_code
    """, (student_id,))
    enrollments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("student_detail.html",
                           student=student,
                           enrollments=enrollments)


# ============================
# ADD STUDENT (CREATE)
# ============================
@main.route("/students/add", methods=["GET", "POST"])
def add_student():
    conn = get_db_connection()
    cur = conn.cursor()

    # load department dropdown
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        year = request.form["year"]
        department_id = request.form["department_id"]

        # basic validation
        if not first or not last or not email or not year or not department_id:
            flash("All fields are required.", "error")
            return render_template("student_add.html", departments=departments)

        cur.execute("""
            INSERT INTO students (department_id, first_name, last_name, email, enrollment_year, status)
            VALUES (%s, %s, %s, %s, %s, 'Active')
        """, (department_id, first, last, email, year))

        conn.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for("main.index"))

    cur.close()
    conn.close()
    return render_template("student_add.html", departments=departments)


# ============================
# EDIT STUDENT
# ============================
@main.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # fetch student
    cur.execute("""
        SELECT student_id, first_name, last_name, email,
               enrollment_year, gpa, status, department_id
        FROM students
        WHERE student_id = %s
    """, (student_id,))
    student = cur.fetchone()

    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("main.index"))

    # departments for dropdown
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    # POST update
    if request.method == "POST":
        first = request.form.get("first_name")
        last = request.form.get("last_name")
        email = request.form.get("email")
        year = request.form.get("enrollment_year")
        status = request.form.get("status")
        department_id = request.form.get("department_id")

        if not first or not last or not email or not year or not department_id:
            flash("All fields are required.", "error")
            return render_template("student_edit.html",
                                   student=student,
                                   departments=departments)

        cur.execute("""
            UPDATE students
            SET first_name=%s, last_name=%s, email=%s,
                enrollment_year=%s, status=%s, department_id=%s
            WHERE student_id=%s
        """, (first, last, email, year, status, department_id, student_id))

        conn.commit()
        flash("Student updated successfully!", "success")
        return redirect(url_for("main.student_detail", student_id=student_id))

    cur.close()
    conn.close()
    return render_template("student_edit.html",
                           student=student,
                           departments=departments)


# ============================
# SOFT DELETE STUDENT
# ============================
@main.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE students
        SET status='Inactive'
        WHERE student_id=%s
    """, (student_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("main.index"))


# ============================
# COURSE LIST
# ============================
@main.route("/courses")
def course_list():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT course_id, course_code, course_name, credits, capacity
        FROM courses
        ORDER BY course_code
    """)
    courses = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("courses.html", courses=courses)


# ============================
# COURSE DETAIL
# ============================
@main.route("/courses/<int:course_id>")
def course_detail(course_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.course_id, c.course_code, c.course_name, c.credits,
               c.level, c.capacity,
               d.department_name,
               i.first_name || ' ' || i.last_name AS instructor_name
        FROM courses c
        JOIN departments d ON c.department_id = d.department_id
        JOIN instructors i ON c.instructor_id = i.instructor_id
        WHERE c.course_id = %s
    """, (course_id,))
    course = cur.fetchone()

    if not course:
        abort(404)

    cur.execute("""
        SELECT s.student_id,
               s.first_name || ' ' || s.last_name AS student_name,
               e.status,
               e.grade
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        WHERE e.course_id = %s
        ORDER BY s.student_id
    """, (course_id,))
    enrollments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("course_detail.html",
                           course=course,
                           enrollments=enrollments)
