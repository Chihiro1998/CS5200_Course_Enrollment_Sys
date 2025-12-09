------------------------------------------------------------
-- final_project.sql
-- Course Enrollment Management System
-- Full schema, sample data, functions, triggers
------------------------------------------------------------

------------------------------------------------------------
-- 0. Drop existing tables (prepare for clean rebuild)
------------------------------------------------------------
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS instructors CASCADE;
DROP TABLE IF EXISTS semesters CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

------------------------------------------------------------
-- 1. Table: departments
------------------------------------------------------------
CREATE TABLE departments (
    department_id     SERIAL PRIMARY KEY,
    department_code   VARCHAR(10) NOT NULL UNIQUE,
    department_name   VARCHAR(100) NOT NULL UNIQUE,
    description       TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

------------------------------------------------------------
-- 2. Table: instructors
------------------------------------------------------------
CREATE TABLE instructors (
    instructor_id   SERIAL PRIMARY KEY,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id)
                      ON DELETE RESTRICT ON UPDATE CASCADE,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    title           VARCHAR(50),
    hire_date       DATE
);

------------------------------------------------------------
-- 3. Table: students
------------------------------------------------------------
CREATE TABLE students (
    student_id        SERIAL PRIMARY KEY,
    department_id     INTEGER REFERENCES departments(department_id)
                        ON DELETE SET NULL ON UPDATE CASCADE,
    first_name        VARCHAR(50) NOT NULL,
    last_name         VARCHAR(50) NOT NULL,
    email             VARCHAR(120) NOT NULL UNIQUE,
    date_of_birth     DATE,
    enrollment_year   INTEGER CHECK (
                          enrollment_year >= 1900 
                          AND enrollment_year <= EXTRACT(YEAR FROM CURRENT_DATE)
                       ),
    gpa               NUMERIC(3,2) CHECK (gpa >= 0 AND gpa <= 4.00),
    status            VARCHAR(20) NOT NULL DEFAULT 'Active'
);

------------------------------------------------------------
-- 4. Table: semesters
------------------------------------------------------------
CREATE TABLE semesters (
    semester_id   SERIAL PRIMARY KEY,
    term          VARCHAR(10) NOT NULL,
    year          INTEGER NOT NULL CHECK (year >= 2000),
    start_date    DATE NOT NULL,
    end_date      DATE NOT NULL,
    UNIQUE(term, year),
    CHECK (end_date > start_date)
);

------------------------------------------------------------
-- 5. Table: courses
------------------------------------------------------------
CREATE TABLE courses (
    course_id      SERIAL PRIMARY KEY,
    department_id  INTEGER NOT NULL REFERENCES departments(department_id)
                     ON DELETE RESTRICT ON UPDATE CASCADE,
    instructor_id  INTEGER NOT NULL REFERENCES instructors(instructor_id)
                     ON DELETE RESTRICT ON UPDATE CASCADE,
    course_code    VARCHAR(20) NOT NULL UNIQUE,
    course_name    VARCHAR(200) NOT NULL,
    credits        INTEGER NOT NULL CHECK (credits > 0 AND credits <= 10),
    description    TEXT,
    capacity       INTEGER NOT NULL CHECK (capacity > 0),
    level          VARCHAR(20),
    status         VARCHAR(20) NOT NULL DEFAULT 'Active'
);

------------------------------------------------------------
-- 6. Table: enrollments
------------------------------------------------------------
CREATE TABLE enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(student_id)
                      ON DELETE CASCADE ON UPDATE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id)
                      ON DELETE CASCADE ON UPDATE CASCADE,
    semester_id     INTEGER NOT NULL REFERENCES semesters(semester_id)
                      ON DELETE CASCADE ON UPDATE CASCADE,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'Enrolled',
    grade           VARCHAR(5),
    UNIQUE(student_id, course_id, semester_id)
);

------------------------------------------------------------
-- 7. Indexes
------------------------------------------------------------
CREATE INDEX idx_courses_department ON courses(department_id);
CREATE INDEX idx_courses_instructor ON courses(instructor_id);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_semester ON enrollments(semester_id);

------------------------------------------------------------
-- 8. Sample Data: departments
------------------------------------------------------------
INSERT INTO departments (department_code, department_name, description) VALUES
('CS',   'Computer Science', 'Department of Computer Science'),
('MATH', 'Mathematics',      'Department of Mathematics'),
('ENG',  'English',          'Department of English'),
('BIO',  'Biology',          'Department of Biological Sciences'),
('PHYS', 'Physics',          'Department of Physics');

------------------------------------------------------------
-- 9. Sample Data: instructors
------------------------------------------------------------
INSERT INTO instructors (department_id, first_name, last_name, email, title, hire_date) VALUES
(1, 'John',   'Smith',   'john.smith@univ.edu',  'Professor',           '2010-08-15'),
(1, 'Sarah',  'Johnson','sarah.johnson@univ.edu','Associate Professor', '2015-01-10'),
(2, 'Michael','Brown',   'michael.brown@univ.edu','Professor',          '2008-09-01'),
(3, 'Emily',  'Davis',   'emily.davis@univ.edu', 'Lecturer',           '2018-08-20'),
(4, 'James',  'Wilson',  'james.wilson@univ.edu','Assistant Professor','2020-01-15');

------------------------------------------------------------
-- 10. Sample Data: students
------------------------------------------------------------
INSERT INTO students (department_id, first_name, last_name, email, enrollment_year, status) VALUES
(1, 'Alice',   'Anderson','alice.anderson@student.edu', 2020, 'Active'),
(1, 'Bob',     'Baker',   'bob.baker@student.edu',      2019, 'Active'),
(2, 'Charlie', 'Clark',   'charlie.clark@student.edu',  2021, 'Active'),
(3, 'Diana',   'Davis',   'diana.davis@student.edu',    2020, 'Active'),
(4, 'Eve',     'Evans',   'eve.evans@student.edu',      2018, 'Graduated'),
(1, 'Frank',  'Foster',  'frank.foster@student.edu',   2022, 'Active'),
(2, 'Grace',  'Green',   'grace.green@student.edu',    2023, 'Active'),
(3, 'Henry',  'Hall',    'henry.hall@student.edu',     2021, 'Active'),
(4, 'Ivy',    'Irwin',   'ivy.irwin@student.edu',      2022, 'Active'),
(5, 'Jack',   'Johnson', 'jack.johnson@student.edu',   2020, 'Active');

------------------------------------------------------------
-- 11. Sample Data: semesters
------------------------------------------------------------
INSERT INTO semesters (term, year, start_date, end_date) VALUES
('Fall',   2024, '2024-09-01', '2024-12-20'),
('Spring', 2025, '2025-01-15', '2025-05-15'),
('Fall',   2025, '2025-09-01', '2025-12-20');

------------------------------------------------------------
-- 12. Sample Data: courses
------------------------------------------------------------
INSERT INTO courses (department_id, instructor_id, course_code, course_name, credits, description, capacity, level) VALUES
(1, 1, 'CS5200',    'Database Management Systems', 4, 'Intro to DB and SQL', 30, 'Graduate'),
(1, 2, 'CS5010',    'Programming Design Paradigm',4, 'Advanced programming concepts', 35, 'Graduate'),
(2, 3, 'MATH2331',  'Linear Algebra', 3, 'Matrices and vector spaces', 40, 'Undergraduate'),
(3, 4, 'ENGL1111',  'First Year Writing', 3, 'Academic writing', 25, 'Undergraduate'),
(4, 5, 'BIO2301',   'Genetics', 4, 'Principles of genetics', 30, 'Undergraduate'),
(1, 1, 'CS3000',   'Algorithms & Data Structures',4, 'Algorithm design', 50, 'Undergraduate'),
(2, 3, 'MATH2400', 'Differential Equations',4, 'Differential equations', 35, 'Undergraduate'),
(5, 5, 'PHYS1151', 'Physics I',4, 'Physics fundamentals', 60, 'Undergraduate');

------------------------------------------------------------
-- 13. Sample Data: enrollments
------------------------------------------------------------
INSERT INTO enrollments (student_id, course_id, semester_id, status) VALUES
(1, 1, 3, 'Enrolled'),
(2, 1, 3, 'Enrolled'),
(3, 3, 3, 'Enrolled'),
(1, 2, 3, 'Enrolled');

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 6, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'CS5200';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 7, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'MATH2331';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 8, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'ENGL1111';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 9, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'BIO2301';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 10, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'PHYS1151';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 6, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'CS5010';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 7, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'CS5200';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 8, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'CS3000';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 9, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'MATH2400';

INSERT INTO enrollments (student_id, course_id, semester_id, status)
SELECT 10, course_id, 3, 'Enrolled' FROM courses WHERE course_code = 'CS3000';

------------------------------------------------------------
-- 14. Cleanup existing triggers and functions
------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_enforce_course_capacity ON enrollments;
DROP TRIGGER IF EXISTS trg_update_gpa ON enrollments;
DROP INDEX IF EXISTS idx_unique_active_enrollment;
DROP FUNCTION IF EXISTS enforce_course_capacity() CASCADE;
DROP FUNCTION IF EXISTS update_student_gpa_after_grade() CASCADE;
DROP FUNCTION IF EXISTS calculate_student_gpa(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS get_course_enrollment_count(INTEGER, INTEGER) CASCADE;
DROP PROCEDURE IF EXISTS enroll_student(INTEGER, INTEGER, INTEGER) CASCADE;
DROP PROCEDURE IF EXISTS drop_course(INTEGER, INTEGER, INTEGER) CASCADE;
DROP PROCEDURE IF EXISTS assign_grade(INTEGER, VARCHAR) CASCADE;

------------------------------------------------------------
-- 15. Function: calculate_student_gpa
------------------------------------------------------------
CREATE OR REPLACE FUNCTION calculate_student_gpa(p_student_id INTEGER)
RETURNS NUMERIC(3,2) AS $$
DECLARE
    calculated_gpa NUMERIC(3,2);
BEGIN
    SELECT ROUND(AVG(
        CASE 
            WHEN grade = 'A'  THEN 4.0
            WHEN grade = 'A-' THEN 3.7
            WHEN grade = 'B+' THEN 3.3
            WHEN grade = 'B'  THEN 3.0
            WHEN grade = 'B-' THEN 2.7
            WHEN grade = 'C+' THEN 2.3
            WHEN grade = 'C'  THEN 2.0
            WHEN grade = 'C-' THEN 1.7
            WHEN grade = 'D+' THEN 1.3
            WHEN grade = 'D'  THEN 1.0
            WHEN grade = 'F'  THEN 0.0

            WHEN grade ~ '^[0-9]{1,3}$' THEN 
                CASE 
                    WHEN grade::INTEGER >= 93 THEN 4.0
                    WHEN grade::INTEGER >= 90 THEN 3.7
                    WHEN grade::INTEGER >= 87 THEN 3.3
                    WHEN grade::INTEGER >= 83 THEN 3.0
                    WHEN grade::INTEGER >= 80 THEN 2.7
                    WHEN grade::INTEGER >= 77 THEN 2.3
                    WHEN grade::INTEGER >= 73 THEN 2.0
                    WHEN grade::INTEGER >= 70 THEN 1.7
                    WHEN grade::INTEGER >= 67 THEN 1.3
                    WHEN grade::INTEGER >= 60 THEN 1.0
                    ELSE 0.0
                END
            ELSE NULL
        END
    ), 2) INTO calculated_gpa
    FROM enrollments
    WHERE student_id = p_student_id 
      AND status = 'Completed'
      AND grade IS NOT NULL;

    RETURN COALESCE(calculated_gpa, 0.00);
END;
$$ LANGUAGE plpgsql;

------------------------------------------------------------
-- 16. Function: get_course_enrollment_count
------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_course_enrollment_count(
    p_course_id INTEGER, 
    p_semester_id INTEGER
)
RETURNS INTEGER AS $$
DECLARE
    enrollment_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO enrollment_count
    FROM enrollments
    WHERE course_id = p_course_id 
      AND semester_id = p_semester_id
      AND status = 'Enrolled';

    RETURN COALESCE(enrollment_count, 0);
END;
$$ LANGUAGE plpgsql;

------------------------------------------------------------
-- 17. Procedure: enroll_student
------------------------------------------------------------
CREATE OR REPLACE PROCEDURE enroll_student(
    p_student_id INTEGER,
    p_course_id INTEGER,
    p_semester_id INTEGER
)
LANGUAGE plpgsql AS $$
DECLARE
    v_capacity INTEGER;
    v_current_count INTEGER;
    v_course_name VARCHAR(200);
BEGIN
    SELECT course_name, capacity INTO v_course_name, v_capacity
    FROM courses
    WHERE course_id = p_course_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Course ID % does not exist', p_course_id;
    END IF;

    v_current_count := get_course_enrollment_count(p_course_id, p_semester_id);

    IF v_current_count >= v_capacity THEN
        RAISE EXCEPTION 'Course "%" is full (Capacity: %, Current: %)',
                        v_course_name, v_capacity, v_current_count;
    END IF;

    INSERT INTO enrollments (student_id, course_id, semester_id, status)
    VALUES (p_student_id, p_course_id, p_semester_id, 'Enrolled');
END;
$$;

------------------------------------------------------------
-- 18. Procedure: drop_course
------------------------------------------------------------
CREATE OR REPLACE PROCEDURE drop_course(
    p_student_id INTEGER,
    p_course_id INTEGER,
    p_semester_id INTEGER
)
LANGUAGE plpgsql AS $$
DECLARE
    v_enrollment_id INTEGER;
BEGIN
    SELECT enrollment_id INTO v_enrollment_id
    FROM enrollments
    WHERE student_id = p_student_id
      AND course_id = p_course_id
      AND semester_id = p_semester_id
      AND status = 'Enrolled';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active enrollment for student %, course %, semester %',
                        p_student_id, p_course_id, p_semester_id;
    END IF;

    UPDATE enrollments
    SET status = 'Dropped'
    WHERE enrollment_id = v_enrollment_id;
END;
$$;

------------------------------------------------------------
-- 19. Procedure: assign_grade
------------------------------------------------------------
CREATE OR REPLACE PROCEDURE assign_grade(
    p_enrollment_id INTEGER,
    p_grade VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE enrollments
    SET grade = p_grade,
        status = 'Completed'
    WHERE enrollment_id = p_enrollment_id;
END;
$$;

------------------------------------------------------------
-- 20. Trigger: enforce course capacity
------------------------------------------------------------
CREATE OR REPLACE FUNCTION enforce_course_capacity()
RETURNS TRIGGER AS $$
DECLARE
    v_capacity INTEGER;
    v_current_count INTEGER;
BEGIN
    SELECT capacity INTO v_capacity
    FROM courses
    WHERE course_id = NEW.course_id;

    SELECT COUNT(*) INTO v_current_count
    FROM enrollments
    WHERE course_id = NEW.course_id
      AND semester_id = NEW.semester_id
      AND status = 'Enrolled';

    IF v_current_count >= v_capacity THEN
        RAISE EXCEPTION 'Course is full';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_course_capacity
BEFORE INSERT ON enrollments
FOR EACH ROW
WHEN (NEW.status = 'Enrolled')
EXECUTE FUNCTION enforce_course_capacity();

------------------------------------------------------------
-- 21. Trigger: GPA update after grade assigned
------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_student_gpa_after_grade()
RETURNS TRIGGER AS $$
DECLARE
    v_new_gpa NUMERIC(3,2);
BEGIN
    IF NEW.status = 'Completed' AND NEW.grade IS NOT NULL THEN
        SELECT calculate_student_gpa(NEW.student_id)
        INTO v_new_gpa;

        UPDATE students
        SET gpa = v_new_gpa
        WHERE student_id = NEW.student_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_gpa
AFTER UPDATE ON enrollments
FOR EACH ROW
WHEN (NEW.status = 'Completed')
EXECUTE FUNCTION update_student_gpa_after_grade();

------------------------------------------------------------
-- End of final_project.sql
------------------------------------------------------------
