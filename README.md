# CS5200_Course_Enrollment_Sys

A web-based course enrollment management application built with Flask and PostgreSQL.  
This system supports student management, course management, enrollment tracking, soft deletion logic, and capacity control through database triggers.

---

## 1. Overview

This system provides an administrative interface for managing university students, courses, instructors, and enrollments. It includes soft deletion, enrollment status tracking, dynamic capacity calculations, and trigger-based enforcement to maintain data integrity.

The project satisfies core requirements for a university-level course project including relational modeling, SQL DDL, DML, triggers, stored functions, and a functional web interface.

---

## 2. Features

### Student Management

- Add, edit, and view student information
- Soft deletion (status = 'Inactive')
- Automatic withdrawal from active courses when a student becomes inactive
- GPA validation and enrollment year validation

### Course Management

- Add, edit, view, and soft delete courses (Soft Delte)
- Prevent deletion when students are enrolled, unless confirmed
- Capacity tracking
- Active vs inactive course filtering in the list

### Enrollment Management

- Add enrollments per student
- Status categories: Enrolled, Withdrawn, Completed, Course_Cancelled
- Prevent duplicate enrollment into the same course/semester
- Automatically reduce capacity when students withdraw or when a course is deleted

### Database Logic

- Normalized schema with foreign keys
- Stored functions for business logic
- Triggers for:
  - Enforcing course capacity
  - Updating student GPA after graded course is completed
  - Automatic enrollment withdrawal when student status becomes inactive
  - Course cancellation logic

---

## 3. Technology Stack

**Backend:** Python Flask  
**Database:** PostgreSQL  
**Driver:** psycopg2  
**UI:** HTML, Bootstrap  
**Tools:** DBeaver, pgAdmin

---

## 4. Database Setup

- The entire database schema, sample data, triggers, and stored functions are contained in a single SQL script:db/final_project.sql

- Running this file will:

1. Drop existing tables (safe for development resets)
2. Create schema in correct dependency order
3. Insert sample data
4. Create all triggers and stored functions

---

### 4.1 Create Database

In PostgreSQL or DBeaver:

```sql
CREATE DATABASE course_enrollment_system;
```

### 4.2 Load Full Schema + Sample Data

- Using DBeaver
- Right-click the database → SQL Editor
- Open file → select final_project.sql
- Click Execute SQL Script
  Using psql:

```bash
psql -U postgres -d course_enrollment_system -f sql/final_project.sql

```

### 4.3 Verify Data

```sql
SELECT COUNT(*) FROM students;
SELECT COUNT(*) FROM courses;
SELECT COUNT(*) FROM enrollments;

```
