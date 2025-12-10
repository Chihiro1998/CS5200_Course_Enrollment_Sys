from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import get_db_connection
from datetime import datetime
from psycopg2.extras import RealDictCursor
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

    current_year = datetime.now().year

    # -----------------------
    # POST — save changes
    # -----------------------
    if request.method == "POST":
        first = request.form["first_name"].strip()
        last = request.form["last_name"].strip()
        email = request.form["email"].strip()
        dept = request.form["department_id"]
        year = request.form["enrollment_year"]
        status = request.form["status"]

        # validate year
        if not year.isdigit() or int(year) > current_year:
            flash(f"Enrollment year cannot exceed {current_year}.", "danger")
            return redirect(url_for("main.edit_student", student_id=student_id))

        # validate name
        if not first or not last:
            flash("First and last name are required.", "danger")
            return redirect(url_for("main.edit_student", student_id=student_id))

        # validate email
        if not email:
            flash("Email cannot be empty.", "danger")
            return redirect(url_for("main.edit_student", student_id=student_id))

        try:
            cur.execute("""
                UPDATE students
                SET first_name=%s, last_name=%s, email=%s,
                    department_id=%s, enrollment_year=%s, status=%s
                WHERE student_id=%s
            """, (first, last, email, dept, year, status, student_id))

            conn.commit()
            flash("Student updated successfully!", "success")
            return redirect(url_for("main.student_detail", student_id=student_id))

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("Email already exists. Please use another one.", "danger")
            return redirect(url_for("main.edit_student", student_id=student_id))

    # -----------------------
    # GET — load initial data
    # -----------------------
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

    return render_template(
        "student_edit.html",
        student=student,
        departments=departments,
        current_year=current_year
    )

# -----------------------------
# Soft Delete Student
# -----------------------------


@main.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    """
    Soft delete a student and release course capacity:

    1) Student → Inactive
    2) All active enrollments (status='Enrolled') → Dropped_Inactive
    """

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # 1. Mark student Inactive
        cur.execute("""
            UPDATE students
            SET status='Inactive'
            WHERE student_id=%s
        """, (student_id,))

        # 2. Change ENROLLED → DROPPED_INACTIVE
        cur.execute("""
            UPDATE enrollments
            SET status='Dropped_Inactive'
            WHERE student_id=%s
              AND status='Enrolled'
        """, (student_id,))

        # 3. No need to update courses table.
        # SELECT COUNT(*) WHERE status='Enrolled' will now decrease automatically!

        conn.commit()
        flash("Student set to Inactive. Enrollments marked Dropped_Inactive.", "success")

    except Exception as e:
        conn.rollback()
        flash("Failed to delete student: " + str(e), "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("main.index"))


# ==========================================================
# COURSE CRUD
# ==========================================================

# -----------------------------
# Course List (Active / All)
# -----------------------------
@main.route("/courses")
def course_list():

    # use 'view' instead of 'mode'
    view = request.args.get("view", "active")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if view == "all":
        cur.execute("""
            SELECT c.*,
                (SELECT COUNT(*) FROM enrollments e 
                    WHERE e.course_id = c.course_id AND e.status='Enrolled')
                AS enrolled_count
            FROM courses c
            ORDER BY c.course_code
        """)
    else:
        cur.execute("""
            SELECT c.*,
                (SELECT COUNT(*) FROM enrollments e 
                    WHERE e.course_id = c.course_id AND e.status='Enrolled')
                AS enrolled_count
            FROM courses c
            WHERE c.status = 'Active'
            ORDER BY c.course_code
        """)

    courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("courses.html", courses=courses, view=view)


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
               e.status,
               e.grade,
               sm.term,
               sm.year
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN semesters sm ON e.semester_id = sm.semester_id
        WHERE e.course_id=%s
        ORDER BY sm.year DESC, sm.term DESC, s.student_id
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

    # load instructors WITH full name
    cur.execute("""
        SELECT instructor_id,
               first_name || ' ' || last_name AS instructor_name
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
# Delete Course (redirect to confirm page if needed)
# -----------------------------


@main.route("/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM enrollments
        WHERE course_id = %s AND status = 'Enrolled'
    """, (course_id,))
    count = cur.fetchone()["cnt"]

    cur.close()
    conn.close()

    if count > 0:
        return redirect(url_for("main.confirm_course_delete",
                                course_id=course_id,
                                enrolled=count))

    return force_delete_course(course_id)

# -----------------------------
# Step 2 — Confirm Delete
# -----------------------------


@main.route("/courses/<int:course_id>/delete/confirm")
def confirm_course_delete(course_id):

    enrolled = request.args.get("enrolled", 0)

    return render_template(
        "course_delete_confirm.html",
        course_id=course_id,
        enrolled=int(enrolled)
    )

# -----------------------------
# Step 3 — FORCE DELETE COURSE
# -----------------------------


@main.route("/courses/<int:course_id>/delete/force", methods=["POST"])
def force_delete_course(course_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        UPDATE enrollments
        SET status='Course_Cancelled', grade=NULL
        WHERE course_id=%s AND status='Enrolled'
    """, (course_id,))

    cur.execute("""
        UPDATE courses
        SET status='Inactive'
        WHERE course_id=%s
    """, (course_id,))

    conn.commit()
    cur.close()
    conn.close()

    flash("Course deleted. All enrolled students marked as Course_Cancelled.", "warning")
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
# Instructors List
# -----------------------------


@main.route("/instructors")
def instructor_list():
    view = request.args.get("view", "active")  # add filter toggle

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if view == "all":
        cur.execute("""
            SELECT i.instructor_id, i.first_name, i.last_name, 
                   i.email, i.title, i.status,
                   d.department_name
            FROM instructors i
            JOIN departments d ON i.department_id = d.department_id
            ORDER BY i.last_name
        """)
    else:
        cur.execute("""
            SELECT i.instructor_id, i.first_name, i.last_name, 
                   i.email, i.title, i.status,
                   d.department_name
            FROM instructors i
            JOIN departments d ON i.department_id = d.department_id
            WHERE i.status = 'Active'
            ORDER BY i.last_name
        """)

    instructors = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("instructor_list.html", instructors=instructors, view=view)


@main.route("/instructors/add", methods=["GET", "POST"])
def add_instructor():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":
        dept = request.form["department_id"]
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        title = request.form["title"]

        cur.execute("""
            INSERT INTO instructors (department_id, first_name, last_name, email, title)
            VALUES (%s, %s, %s, %s, %s)
        """, (dept, first, last, email, title))

        conn.commit()
        flash("Instructor added successfully!", "success")
        return redirect(url_for("main.instructor_list"))

    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("instructor_add.html", departments=departments)


@main.route("/instructors/<int:instructor_id>/edit", methods=["GET", "POST"])
def edit_instructor(instructor_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":
        dept = request.form["department_id"]
        first = request.form["first_name"]
        last = request.form["last_name"]
        email = request.form["email"]
        title = request.form["title"]

        cur.execute("""
            UPDATE instructors
            SET department_id=%s, first_name=%s, last_name=%s, email=%s, title=%s
            WHERE instructor_id=%s
        """, (dept, first, last, email, title, instructor_id))

        conn.commit()
        flash("Instructor updated!", "success")
        return redirect(url_for("main.instructor_list"))

    cur.execute("""
        SELECT * FROM instructors WHERE instructor_id=%s
    """, (instructor_id,))
    instructor = cur.fetchone()

    cur.execute("SELECT department_id, department_name FROM departments")
    departments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "instructor_edit.html", instructor=instructor, departments=departments
    )


@main.route("/instructors/<int:instructor_id>")
def instructor_detail(instructor_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT i.*, d.department_name 
        FROM instructors i
        JOIN departments d ON i.department_id = d.department_id
        WHERE instructor_id = %s
    """, (instructor_id,))
    instructor = cur.fetchone()

    if not instructor:
        cur.close()
        conn.close()
        flash("Instructor not found.", "danger")
        return redirect(url_for("main.instructor_list"))

    cur.execute("""
        SELECT 
            c.course_id,
            c.course_code,
            c.course_name,
            c.status,
            c.capacity,
            (
                SELECT COUNT(*) 
                FROM enrollments e
                WHERE e.course_id = c.course_id
                  AND e.status = 'Enrolled'
            ) AS enrolled_count
        FROM courses c
        WHERE c.instructor_id = %s
        ORDER BY c.course_code
    """, (instructor_id,))
    courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "instructor_detail.html",
        instructor=instructor,
        courses=courses
    )


# -----------------------------
# Confirm delete instructor
# -----------------------------


@main.route("/instructors/<int:instructor_id>/confirm_delete")
def confirm_delete_instructor(instructor_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # basic instructor info
    cur.execute("""
        SELECT first_name, last_name
        FROM instructors
        WHERE instructor_id = %s
    """, (instructor_id,))
    instructor = cur.fetchone()

    if not instructor:
        cur.close()
        conn.close()
        flash("Instructor not found.", "danger")
        return redirect(url_for("main.instructor_list"))

    # count active courses taught by this instructor
    cur.execute("""
        SELECT COUNT(*) AS course_count
        FROM courses
        WHERE instructor_id = %s
          AND status = 'Active'
    """, (instructor_id,))
    course_count = cur.fetchone()["course_count"]

    # count active enrollments in those courses
    cur.execute("""
        SELECT COUNT(*) AS enrollment_count
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        WHERE c.instructor_id = %s
          AND c.status = 'Active'
          AND e.status = 'Enrolled'
    """, (instructor_id,))
    enrollment_count = cur.fetchone()["enrollment_count"]

    cur.close()
    conn.close()

    return render_template(
        "instructor_confirm_delete.html",
        instructor_id=instructor_id,
        instructor=instructor,
        course_count=course_count,
        enrollment_count=enrollment_count,
    )


# -----------------------------
# Delete Instructor (soft delete with cascading)
# -----------------------------
@main.route("/instructors/<int:instructor_id>/delete", methods=["POST"])
def delete_instructor(instructor_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # 1. mark instructor as Inactive
        cur.execute("""
            UPDATE instructors
            SET status = 'Inactive'
            WHERE instructor_id = %s
        """, (instructor_id,))

        # 2. collect all active courses taught by this instructor
        cur.execute("""
            SELECT course_id
            FROM courses
            WHERE instructor_id = %s
              AND status = 'Active'
        """, (instructor_id,))
        course_rows = cur.fetchall()
        course_ids = [row["course_id"] for row in course_rows]

        cancelled_enrollments = 0

        if course_ids:
            # 3. mark those courses as Inactive
            cur.execute("""
                UPDATE courses
                SET status = 'Inactive'
                WHERE course_id = ANY(%s)
            """, (course_ids,))

            # 4. mark active enrollments in those courses as Course_Cancelled
            cur.execute("""
                UPDATE enrollments
                SET status = 'Course_Cancelled'
                WHERE course_id = ANY(%s)
                  AND status = 'Enrolled'
            """, (course_ids,))
            cancelled_enrollments = cur.rowcount

        conn.commit()

        msg = "Instructor deleted (soft delete)."
        if course_ids:
            msg += f" {len(course_ids)} active course(s) were inactivated"
            if cancelled_enrollments:
                msg += f" and {cancelled_enrollments} active enrollment(s) were marked as Course_Cancelled."
            else:
                msg += "."
        flash(msg, "success")

    except Exception as e:
        conn.rollback()
        flash("Error deleting instructor. Please try again.", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("main.instructor_list"))

# -----------------------------
# Enrollment List (GLOBAL)
# -----------------------------


@main.route("/enrollments")
def enrollment_list():
    view = request.args.get("view", "active")  # default to active

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if view == "all":
        # ALL enrollments (include inactive students/courses)
        cur.execute("""
            SELECT e.enrollment_id, e.student_id, 
                   s.first_name || ' ' || s.last_name AS student_name,
                   e.course_id, c.course_code, c.course_name,
                   e.status, e.grade,
                   sm.term, sm.year
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            JOIN semesters sm ON e.semester_id = sm.semester_id
            ORDER BY e.enrollment_id ASC
        """)
    else:
        # ACTIVE enrollments only
        cur.execute("""
            SELECT e.enrollment_id, e.student_id,
                   s.first_name || ' ' || s.last_name AS student_name,
                   e.course_id, c.course_code, c.course_name,
                   e.status, e.grade,
                   sm.term, sm.year
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            JOIN semesters sm ON e.semester_id = sm.semester_id
            WHERE e.status = 'Enrolled'
              AND s.status = 'Active'
              AND c.status = 'Active'
            ORDER BY e.enrollment_id ASC
        """)

    enrollments = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("enrollment_list.html", enrollments=enrollments, view=view)


# -----------------------------
# Grade Enrollment
# -----------------------------
@main.route("/enrollments/<int:enrollment_id>/grade", methods=["GET", "POST"])
def grade_enrollment(enrollment_id):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":
        grade = request.form["grade"]

        cur.execute("""
            UPDATE enrollments
            SET grade = %s, status = 'Completed'
            WHERE enrollment_id = %s
        """, (grade, enrollment_id))

        conn.commit()
        cur.close()
        conn.close()

        flash("Grade updated successfully!", "success")
        return redirect(url_for("main.enrollment_list"))

    # GET — load enrollment info
    cur.execute("""
        SELECT e.*, 
               s.first_name || ' ' || s.last_name AS student_name,
               c.course_code, c.course_name
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN courses c ON e.course_id = c.course_id
        WHERE enrollment_id = %s
    """, (enrollment_id,))

    enrollment = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("grade_edit.html", enrollment=enrollment)
