from django.db import models, connection


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if not row:
        return None
    return dict(zip(columns, row))


class AccountManager(models.Manager):

    def create_user_with_raw_sql(self, name, email, password, role):
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO users (name, email, password, role)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, [name, email, password, role])
            return cursor.lastrowid

    def login_with_raw_sql(self, email, password):
        with connection.cursor() as cursor:
            sql = """
                SELECT user_id, name, email, role, is_profile_completed
                FROM users
                WHERE email = %s AND password = %s
            """
            cursor.execute(sql, [email, password])
            return dictfetchone(cursor)

    def get_user_by_id(self, user_id):
        with connection.cursor() as cursor:
            sql = """
                SELECT
                    u.user_id,
                    u.name,
                    u.email,
                    u.role,
                    u.department_id,
                    d.department_name,
                    u.enrollment_year,
                    u.graduation_year,
                    u.company_id,
                    c.name AS company_name,
                    u.current_job_title,
                    u.is_profile_completed
                FROM users u
                LEFT JOIN departments d
                    ON u.department_id = d.department_id
                LEFT JOIN companies c
                    ON u.company_id = c.company_id
                WHERE u.user_id = %s
            """
            cursor.execute(sql, [user_id])
            return dictfetchone(cursor)

    def update_onboarding(self, user_id, department_id, enrollment_year, graduation_year, company_id, current_job_title):
        with connection.cursor() as cursor:
            sql = """
                UPDATE users
                SET department_id = %s,
                    enrollment_year = %s,
                    graduation_year = %s,
                    company_id = %s,
                    current_job_title = %s,
                    is_profile_completed = TRUE
                WHERE user_id = %s
            """
            cursor.execute(sql, [
                department_id,
                enrollment_year,
                graduation_year,
                company_id,
                current_job_title,
                user_id
            ])

    def update_profile(self, user_id, department_id, enrollment_year, graduation_year, company_id, current_job_title):
        with connection.cursor() as cursor:
            sql = """
                UPDATE users
                SET department_id = %s,
                    enrollment_year = %s,
                    graduation_year = %s,
                    company_id = %s,
                    current_job_title = %s
                WHERE user_id = %s
            """
            cursor.execute(sql, [
                department_id,
                enrollment_year,
                graduation_year,
                company_id,
                current_job_title,
                user_id
            ])


class ActivityManager(models.Manager):

    def add_activity(self, user_id, category, title, role, start_date, end_date, description):
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO activities
                (user_id, category, title, role, start_date, end_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, [
                user_id, category, title, role, start_date, end_date, description
            ])

    def get_user_activities(self, user_id):
        with connection.cursor() as cursor:
            sql = """
                SELECT activity_id, user_id, category, title, role,
                       start_date, end_date, description
                FROM activities
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(sql, [user_id])
            return dictfetchall(cursor)

    def update_activity(self, activity_id, user_id, category, title, role, start_date, end_date, description):
        with connection.cursor() as cursor:
            sql = """
                UPDATE activities
                SET category = %s,
                    title = %s,
                    role = %s,
                    start_date = %s,
                    end_date = %s,
                    description = %s
                WHERE activity_id = %s AND user_id = %s
            """
            cursor.execute(sql, [
                category, title, role, start_date, end_date, description,
                activity_id, user_id
            ])

    def delete_activity(self, activity_id, user_id):
        with connection.cursor() as cursor:
            sql = """
                DELETE FROM activities
                WHERE activity_id = %s AND user_id = %s
            """
            cursor.execute(sql, [activity_id, user_id])


class WorkExperienceManager(models.Manager):

    def add_work(self, user_id, company_id, job_type, job_title, start_date, end_date, description):
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO work_experiences
                (user_id, company_id, job_type, job_title, start_date, end_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, [
                user_id, company_id, job_type, job_title, start_date, end_date, description
            ])

    def get_user_work_experiences(self, user_id):
        with connection.cursor() as cursor:
            sql = """
                SELECT
                    w.work_id,
                    w.user_id,
                    w.company_id,
                    c.name AS company_name,
                    w.job_type,
                    w.job_title,
                    w.start_date,
                    w.end_date,
                    w.description
                FROM work_experiences w
                JOIN companies c
                    ON w.company_id = c.company_id
                WHERE w.user_id = %s
                ORDER BY w.created_at DESC
            """
            cursor.execute(sql, [user_id])
            return dictfetchall(cursor)

    def update_work(self, work_id, user_id, company_id, job_type, job_title, start_date, end_date, description):
        with connection.cursor() as cursor:
            sql = """
                UPDATE work_experiences
                SET company_id = %s,
                    job_type = %s,
                    job_title = %s,
                    start_date = %s,
                    end_date = %s,
                    description = %s
                WHERE work_id = %s AND user_id = %s
            """
            cursor.execute(sql, [
                company_id, job_type, job_title, start_date, end_date, description,
                work_id, user_id
            ])

    def delete_work(self, work_id, user_id):
        with connection.cursor() as cursor:
            sql = """
                DELETE FROM work_experiences
                WHERE work_id = %s AND user_id = %s
            """
            cursor.execute(sql, [work_id, user_id])


class CourseRecordManager(models.Manager):

    def add_course(self, user_id, course_name, semester, grade):
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO course_records
                (user_id, course_name, semester, grade)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, [user_id, course_name, semester, grade])

    def get_user_courses(self, user_id):
        with connection.cursor() as cursor:
            sql = """
                SELECT course_record_id, user_id, course_name, semester, grade
                FROM course_records
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(sql, [user_id])
            return dictfetchall(cursor)

    def update_course(self, course_record_id, user_id, course_name, semester, grade):
        with connection.cursor() as cursor:
            sql = """
                UPDATE course_records
                SET course_name = %s,
                    semester = %s,
                    grade = %s
                WHERE course_record_id = %s AND user_id = %s
            """
            cursor.execute(sql, [
                course_name, semester, grade,
                course_record_id, user_id
            ])

    def delete_course(self, course_record_id, user_id):
        with connection.cursor() as cursor:
            sql = """
                DELETE FROM course_records
                WHERE course_record_id = %s AND user_id = %s
            """
            cursor.execute(sql, [course_record_id, user_id])


class CourseTagManager(models.Manager):

    def get_all_tags(self):
        with connection.cursor() as cursor:
            sql = """
                SELECT tag_id, tag_name
                FROM course_tags
                ORDER BY tag_name
            """
            cursor.execute(sql)
            return dictfetchall(cursor)

    def get_tags_by_course_record(self, course_record_id):
        with connection.cursor() as cursor:
            sql = """
                SELECT ct.tag_id, ct.tag_name
                FROM course_record_tags crt
                JOIN course_tags ct
                    ON crt.tag_id = ct.tag_id
                WHERE crt.course_record_id = %s
                ORDER BY ct.tag_name
            """
            cursor.execute(sql, [course_record_id])
            return dictfetchall(cursor)


class CompanyManager(models.Manager):

    def get_all_companies(self):
        with connection.cursor() as cursor:
            sql = """
                SELECT company_id, name
                FROM companies
                ORDER BY name
            """
            cursor.execute(sql)
            return dictfetchall(cursor)


class DepartmentManager(models.Manager):

    def get_all_departments(self):
        with connection.cursor() as cursor:
            sql = """
                SELECT department_id, department_name
                FROM departments
                ORDER BY department_id
            """
            cursor.execute(sql)
            return dictfetchall(cursor)


class Department(models.Model):
    class Meta:
        db_table = 'departments'
        managed = False

    objects = DepartmentManager()


class Company(models.Model):
    class Meta:
        db_table = 'companies'
        managed = False

    objects = CompanyManager()


class CourseRecord(models.Model):
    class Meta:
        db_table = 'course_records'
        managed = False

    objects = CourseRecordManager()


class CourseTag(models.Model):
    class Meta:
        db_table = 'course_tags'
        managed = False

    objects = CourseTagManager()


class WorkExperience(models.Model):
    class Meta:
        db_table = 'work_experiences'
        managed = False

    objects = WorkExperienceManager()


class Activity(models.Model):
    class Meta:
        db_table = 'activities'
        managed = False

    objects = ActivityManager()


class Account(models.Model):
    class Meta:
        db_table = 'users'
        managed = False

    objects = AccountManager()