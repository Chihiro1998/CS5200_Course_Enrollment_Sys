from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort
)
from .models import get_db_connection

# =====================================================
# Blueprint
# =====================================================
main = Blueprint("main", __name__)

# =====================================================
# STUDENT ROUTES
# =====================================================


@main.route("/")
def index():
    """Student list page"""
    conn = get_db_connection()
    cur = conn.cursor()
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


@main.route("/students/<int:student_id>")
def student_detail(student_id):
    """Student detail page"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.student_id, s.first_name, s.last_name, s.email,
               s.enrollment_year, s.gpa, s.status,
               d.department_name
        FROM students s
        LEFT JOIN departments d ON s.department_id = d.department_id
        WHERE s.student_id = %s
    """, (student_id,))
    student = cur.fetchone()

    if not student:
        abort(404)

    cur.execute("""
        SELECT e.enrollment_id, c.course_code, c.course_name,
               sm.term, sm.year, e.status, e.grade
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        JOIN semesters sm ON e.semester_id = sm.semester_id
        WHERE e.student_id = %s
        ORDER BY sm.year DESC, sm.term DESC
    """, (student_id,))
    enrollments = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("student_detail.html",
                           student=student,
                           enrollments=enrollments)


@main.route("/students/add", methods=["GET", "POST"])
def add_student():
    """Create new student"""
    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        dept = request.form["department_id"]
        year = request.form["enrollment_year"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO students (first_name, last_name, email,
                                  department_id, enrollment_year, status)
            VALUES (%s, %s, %s, %s, %s, 'Active')
        """, (first, last, email, dept, year))

        conn.commit()
        cur.close()
        conn.close()

        flash("Student added successfully!", "success")
        return redirect(url_for("main.index"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("student_add.html", departments=departments)


@main.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    """Edit student info"""
    conn = get_db_connection()
    cur = conn.cursor()

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
        cur.close()
        conn.close()

        flash("Student updated successfully!", "success")
        return redirect(url_for("main.student_detail", student_id=student_id))

    # GET - fetch student
    cur.execute("""
        SELECT student_id, first_name, last_name, email,
               enrollment_year, gpa, status, department_id
        FROM students
        WHERE student_id=%s
    """, (student_id,))
    student = cur.fetchone()

    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("student_edit.html",
                           student=student,
                           departments=departments)


@main.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    """Soft delete a student"""
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

    flash("Student has been deactivated (soft delete).", "success")
    return redirect(url_for("main.index"))


# =====================================================
# COURSE ROUTES
# =====================================================

@main.route("/courses")
def course_list():
    """Course list page"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT course_id, course_code, course_name,
               credits, capacity
        FROM courses
        WHERE status='Active'
        ORDER BY course_code
    """)
    courses = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("courses.html", courses=courses)


@main.route("/course/<int:course_id>")
def course_detail(course_id):
    """Course detail page"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.course_id, c.course_code, c.course_name, c.credits,
               c.level, c.capacity, d.department_name,
               i.first_name || ' ' || i.last_name AS instructor_name
        FROM courses c
        JOIN departments d ON c.department_id = d.department_id
        JOIN instructors i ON c.instructor_id = i.instructor_id
        WHERE c.course_id=%s
    """, (course_id,))
    course = cur.fetchone()

    if not course:
        abort(404)

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

    return render_template("course_detail.html",
                           course=course,
                           enrollments=enrollments)


@main.route("/courses/add", methods=["GET", "POST"])
def add_course():
    """Add new course"""
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        code = request.form["course_code"]
        name = request.form["course_name"]
        credits = request.form["credits"]
        capacity = request.form["capacity"]
        level = request.form["level"]
        dept = request.form["department_id"]
        instructor = request.form["instructor_id"]

        cur.execute("""
            INSERT INTO courses (course_code, course_name, credits,
                                 capacity, level, department_id,
                                 instructor_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (code, name, credits, capacity, level, dept, instructor))

        conn.commit()
        cur.close()
        conn.close()

        flash("Course added successfully!", "success")
        return redirect(url_for("main.course_list"))

    # GET load dropdown lists
    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.execute("""
        SELECT instructor_id, first_name || ' ' || last_name
        FROM instructors
    """)
    instructors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("course_add.html",
                           departments=departments,
                           instructors=instructors)


@main.route("/course/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    """Edit existing course"""
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        code = request.form["course_code"]
        name = request.form["course_name"]
        credits = request.form["credits"]
        capacity = request.form["capacity"]
        level = request.form["level"]
        dept = request.form["department_id"]
        instructor = request.form["instructor_id"]

        cur.execute("""
            UPDATE courses
            SET course_code=%s, course_name=%s, credits=%s,
                capacity=%s, level=%s,
                department_id=%s, instructor_id=%s
            WHERE course_id=%s
        """, (code, name, credits, capacity, level, dept, instructor, course_id))

        conn.commit()
        cur.close()
        conn.close()

        flash("Course updated successfully!", "success")
        return redirect(url_for("main.course_detail", course_id=course_id))

    # GET - load course data
    cur.execute("""
        SELECT course_id, course_code, course_name,
               credits, capacity, level,
               department_id, instructor_id
        FROM courses
        WHERE course_id=%s
    """, (course_id,))
    course = cur.fetchone()

    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.execute("""
        SELECT instructor_id, first_name || ' ' || last_name
        FROM instructors
    """)
    instructors = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("course_edit.html",
                           course=course,
                           departments=departments,
                           instructors=instructors)


@main.route("/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    """Soft delete course"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE courses
        SET status='Inactive'
        WHERE course_id=%s
    """, (course_id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("Course has been deleted (soft delete).", "success")
    return redirect(url_for("main.course_list"))
