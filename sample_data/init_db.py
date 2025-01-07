import psycopg2
import csv
import bcrypt

# Database connection details
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "mysecretpassword"
DB_PORT = "5432"

try:
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SET datestyle TO ISO, DMY;")
    # Create database 'ice' if it doesn't exist
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='ice';")
    exists = cursor.fetchone()
    if exists:
        print("Database 'ice' already exists. dropping")
        cursor.execute("DROP DATABASE ice;")
        conn.commit()
    cursor.execute("CREATE DATABASE ice;")
    conn.commit()
    

    # Connect to the new database
    conn.close()
    conn = psycopg2.connect(
        host=DB_HOST, database="ice", user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )
    cursor = conn.cursor()

    # Create 'departments' table
    create_departments_query = """
    CREATE TABLE IF NOT EXISTS departments (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        key VARCHAR(50) NOT NULL UNIQUE
    );
    """
    cursor.execute(create_departments_query)
    print("Table 'departments' created successfully or already exists.")

    # Insert predefined departments
    cursor.execute(
        """INSERT INTO departments (name, key) VALUES 
        ('ΣΧΟΛΗ ΜΗΑΝΙΚΩΝ ΥΠΟΛΙΣΤΩΝ', 'ice'), 
        ('ΒΙΒΛΙΟΘΗΚΟΝΟΜΙΑ', 'lib')
        ON CONFLICT (key) DO NOTHING;"""
    )
    conn.commit()
    print("Predefined departments inserted successfully.")

    create_department_secretariats = """
    CREATE TABLE IF NOT EXISTS department_secretariats (
        id SERIAL PRIMARY KEY,         
        department_id INT NOT NULL,
        email VARCHAR(100) NOT NULL,
        contact_phone VARCHAR(50) NOT NULL,
        address TEXT,
        working_hours VARCHAR(100),
        website_url VARCHAR(255),
        CONSTRAINT fk_department FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE CASCADE
    );
    """
    cursor.execute(create_department_secretariats)
    conn.commit()
    print("Table 'department_secretariats' created successfully or already exists..")

    create_insert_department_secretariats = """
    INSERT INTO department_secretariats (department_id, email, contact_phone, address, working_hours, website_url)
    VALUES
        (1, 'ice@uniwa.gr', '210538-5382/5308/5309/5384', '', 'Δευτ-Τετ-Παρ, 9:00-13:00', 'http://www.ice.uniwa.gr'),
        (2, 'alis@uniwa.gr', '2105385203', '', 'Δευτ-Τετ-Παρ, 10:00-14:00', 'http://alis.uniwa.gr')
    ;
    """
    cursor.execute(create_insert_department_secretariats)
    conn.commit()
    print("Data inserted on 'department_secretariats' successfully.")

    create_roles_query = """
    CREATE TABLE IF NOT EXISTS roles (
        role_id SERIAL PRIMARY KEY,
        role_name VARCHAR(50) NOT NULL UNIQUE
    );
    """
    cursor.execute(create_roles_query)
    print("Table 'roles' created successfully or already exists.")

    # Insert predefined roles
    cursor.execute(
        """
        INSERT INTO roles (role_name)
        VALUES ('student'), ('teacher')
        ON CONFLICT (role_name) DO NOTHING;
        """
    )
    conn.commit()
    print("Predefined roles inserted successfully.")

    create_users_query = """
        CREATE TABLE IF NOT EXISTS users (
    	user_id SERIAL PRIMARY KEY,
    	first_name VARCHAR(50) ,
    	last_name VARCHAR(50) NOT NULL,
    	email VARCHAR(100) UNIQUE NOT NULL,
    	date_of_birth DATE,
    	enrollment_date DATE NOT NULL,
    	department_id INT NOT NULL,
    	gender VARCHAR(20) NOT NULL,
    	role_id INT NOT NULL DEFAULT '1',
    	CONSTRAINT fk_role_id FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE SET NULL,
        CONSTRAINT fk_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
	);
    """
    cursor.execute(create_users_query)
    print("Table 'students' updated successfully.")

    create_user_credentials_query = """
        CREATE TABLE IF NOT EXISTS user_credentials (
        id SERIAL PRIMARY KEY,
        user_id INT UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
    );
    """

    cursor.execute(create_user_credentials_query)
    print("Table 'user_credentials' created successfully or already exists.")

    # Create 'classes' table
    create_classes_query = """
    CREATE TABLE IF NOT EXISTS classes (
        class_id SERIAL PRIMARY KEY,
        class_name VARCHAR(100) NOT NULL,
        class_type VARCHAR(100) NOT NULL,
    	department_id INT NOT NULL,
        program VARCHAR(50) NOT NULL DEFAULT 'ΠΡΟΠΤΥΧΙΑΚΟ',
        semester INT NOT NULL,
        CONSTRAINT fk_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
    );
    """
    cursor.execute(create_classes_query)
    print("Table 'classes' created successfully or already exists.")

    conn.commit()

    with open('./classes.csv', 'r') as f:
        next(f)
        reader = csv.reader(f)
        
        for row in reader:
            cursor.execute(
                """
                INSERT INTO classes (department_id,semester,class_name, class_type, program)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (row[0], row[1], row[2],row[3],row[4])
            )
    conn.commit()
    print("classes.csv imported")

    # # Create the class_schedules table
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS class_schedules (
        id SERIAL PRIMARY KEY,
        semester INT NOT NULL,
        class_team INT NOT NULL DEFAULT 1,
        teacher_id INT NOT NULL,
        class_id INT NOT NULL,
        classroom VARCHAR(50) NOT NULL,
        day_of_week INTEGER NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        FOREIGN KEY (class_id) REFERENCES classes (class_id),
        FOREIGN KEY (teacher_id) REFERENCES users (user_id)
    );
    '''
    # Execute the query
    cursor.execute(create_table_query)
    print("Table 'class_schedules' created successfully or already exists.")
    # Create an index for fast querying
    create_index_query = '''
    CREATE INDEX IF NOT EXISTS idx_class_schedule
    ON class_schedules (day_of_week, start_time, end_time);
    '''
    cursor.execute(create_index_query)

    # SELECT * 
    # FROM student_info
    # WHERE special_needs @> '["dyslexia"]';
    # INSERT INTO student_info (am, semester, special_needs) 
    # VALUES ('AM1234', 3, '["dyslexia", "hearing_impairment"]');
    create_student_info_query = '''
    CREATE TABLE IF NOT EXISTS student_info (
        id SERIAL PRIMARY KEY,
        user_id INT UNIQUE NOT NULL,
        am VARCHAR(50) UNIQUE NOT NULL,
        semester INT NOT NULL,
        special_needs JSONB DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    '''
    cursor.execute(create_student_info_query)
    conn.commit()
    print("Table student_info generated or exists")

    with open('./students.csv', 'r') as f:
        next(f)
        reader = csv.reader(f)
        id=1
        for row in reader:
            cursor.execute("SET datestyle TO ISO, DMY;")
            cursor.execute(
                """
                INSERT INTO users (first_name, last_name,email,date_of_birth,enrollment_date,department_id,gender,role_id)
                VALUES (%s, %s,%s, %s,%s, %s,%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8])
            )
            conn.commit()
            cursor.execute(f"SELECT key FROM departments WHERE id = {row[6]} LIMIT 1")
            department_key=cursor.fetchone()
            cursor.execute('''
                INSERT INTO student_info (user_id, am, semester, special_needs)
                VALUES (%s, %s, %s,%s)
                ''',
                (id,f'{department_key[0]}{id}',row[9],None)
            )
            conn.commit()
            id+=1

    print("Data from 'students.csv' inserted successfully.")        
    print("Student info generated")

    with open('./teachers.csv','r') as f:
        next(f)
        reader = csv.reader(f)
        
        for row in reader:
            cursor.execute("SET datestyle TO ISO, DMY;")
            cursor.execute(
                """
                INSERT INTO users (first_name, last_name,email,date_of_birth,enrollment_date,department_id,gender,role_id)
                VALUES (%s, %s,%s, %s,%s, %s,%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8])
            )
    conn.commit()
    print("Data from 'teachers.csv' inserted successfully.")

    with open('./students.csv', 'r') as f:
        next(f)
        reader = csv.reader(f)
        
        for row in reader:
            hashed_password = bcrypt.hashpw('StronkP@ssw0rd'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                """
                INSERT INTO user_credentials (user_id, password_hash)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (row[0], hashed_password)
            )
    conn.commit()
    print("Passwords for users created successfully.")

    with open('./teachers.csv', 'r') as f:
        next(f)
        reader = csv.reader(f)
        
        for row in reader:
            hashed_password = bcrypt.hashpw('StronkP@ssw0rd'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                """
                INSERT INTO user_credentials (user_id, password_hash)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (row[0], hashed_password)
            )
    conn.commit()
    print("Passwords for teachers created successfully.")

    with open('./schedule.csv', 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:

            teacher_last_name = row[2].strip()  # Strip whitespace
            print(f"Looking for teacher: '{teacher_last_name}'")
            lookup_teacher_query = '''
            SELECT user_id FROM users WHERE last_name = %s LIMIT 1;
            '''
            # Execute query
            cursor.execute(lookup_teacher_query, (teacher_last_name,))
            teacher_id = cursor.fetchone()
            if teacher_id==None:
                print("teacher name missmatch, skipping")
                continue
            print(f"found for teacher: '{teacher_id[0]}'")
            if teacher_id:
                teacher_id = teacher_id[0]
            else:
                print(f"Teacher '{row[2]}' not found. fix the init data and retry.")
                break

            lookup_class_query = '''
            SELECT class_id,semester FROM classes WHERE class_name = %s LIMIT 1;
            '''
            cursor.execute(lookup_class_query, (row[1],))
            class_res = cursor.fetchone()
            if class_res==None:
                print("class name missmatch, skipping")
                continue
            print(f"found class id: '{class_res[0]}'")
            if class_res:
                class_id = class_res[0]
                semester = class_res[1]
            else:
                print(f"class '{row[2]}' not found. fix the init data and retry.")
                break

            cursor.execute(
                """
                INSERT INTO class_schedules (semester,class_team,class_id,teacher_id,classroom,start_time,end_time,day_of_week)
                VALUES (%s, %s, %s,%s, %s, %s,%s, %s);
                """,
                (semester, row[0], class_id,teacher_id,row[3], row[4], row[5],row[6])
            )
    conn.commit()
    print("Schedules generated")

    create_student_enrollments_query = """
    CREATE TABLE IF NOT EXISTS student_enrollments (
        enrollment_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        class_id INT NOT NULL,
        enrollment_date TIMESTAMPTZ DEFAULT NOW(),
        department_id INT NOT NULL,
        CONSTRAINT fk_user
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        CONSTRAINT fk_class
            FOREIGN KEY (class_id) REFERENCES classes (class_id) ON DELETE CASCADE,
        CONSTRAINT fk_department
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
        UNIQUE (user_id, class_id)
    );"""

    cursor.execute(create_student_enrollments_query)
    conn.commit()
    print("Table student_enrollments created successfully.")

    with open('./students.csv', 'r') as f:
        next(f)
        reader = csv.reader(f)
        
        for row in reader:
            user_team = 1
            if row[6]==1:
                if row[9] == 1:
                    if row[0] % 10 in (7, 8, 9):
                        user_team=2
                else:
                    if row[0] % 2 == 1:
                        user_team=2

            cursor.execute(f"SELECT class_id FROM classes WHERE semester={row[9]} and department_id={row[6]};")
            classes = cursor.fetchall()
            for uni_class in classes:
                cursor.execute('''
                    INSERT INTO student_enrollments (department_id, user_id, class_id)
                    VALUES (%s, %s, %s)
                    ''',
                    (row[6], row[0],uni_class[0])
                )
    conn.commit()
    print("Student enrollments have been generated")

    if conn:
        cursor.close()
        conn.close()
        print("Database connection closed.")
except NameError as e:
    print(f"Connection was not established, skipping closure. {e}")
except Exception as e:
    print(f"An error occurred: {e}")
    