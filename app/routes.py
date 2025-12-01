from flask import Blueprint, render_template, abort
from .models import get_db_connection

main = Blueprint("main", __name__)

# ======================================
# HomePage
# ======================================


@main.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT student_id, first_name, last_name 
        FROM students 
        ORDER BY student_id
    """)
    students = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", students=students)


# ======================================
# Student Detail Page
# ======================================
@main.route("/students/<int:student_id>")
def student_detail(student_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # ---- 1. get Student base information ----
    cur.execute("""
        SELECT student_id, first_name, last_name, email, gpa
        FROM students
        WHERE student_id = %s
    """, (student_id,))
    student = cur.fetchone()

    if student is None:
        cur.close()
        conn.close()
        abort(404)

    # ---- 2. Get enrollments for all student----
    cur.execute("""
        SELECT 
            e.enrollment_id,
            c.course_code,
            c.course_name,
            s.term,
            s.year,
            e.status,
            e.grade
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        JOIN semesters s ON e.semester_id = s.semester_id
        WHERE e.student_id = %s
        ORDER BY s.year, s.term, c.course_code;
    """, (student_id,))
    enrollments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "student_detail.html",
        student=student,
        enrollments=enrollments
    )
