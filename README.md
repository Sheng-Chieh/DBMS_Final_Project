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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);