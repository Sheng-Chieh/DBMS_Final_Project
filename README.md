# DBMS_Final_Project
1.在 TablePlus 建立資料庫 final_project
2.複製下面的表 → 貼到 TablePlus → Run
3.執行 data_insert.py（公司資料）
4.跑 Django

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    role ENUM('student', 'alumni') NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    department_id INT,
    enrollment_year INT,
    graduation_year INT,
    current_company VARCHAR(100),
    current_job_title VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    company_id INT
    is_profile_completed BOOLEAN DEFAULT FALSE
);
CREATE TABLE course_records (
    course_record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    course_category VARCHAR(50),
    semester VARCHAR(50),
    grade VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE work_experiences (
    work_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    job_type VARCHAR(50),
    company_name VARCHAR(100) NOT NULL,
    job_title VARCHAR(100),
    start_date DATE,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE activities (
    activity_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(50),
    title VARCHAR(100) NOT NULL,
    role VARCHAR(100),
    start_date DATE,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);