-- NotesApp schema + seed. Loaded automatically by postgres on first start
-- (docker-entrypoint-initdb.d). Runs only when the data volume is empty.

DROP TABLE IF EXISTS notes, enrollments, classes, users CASCADE;

CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,          -- stored in clear text (planted flaw #1)
    role       TEXT NOT NULL,          -- 'student' | 'teacher' | 'admin'
    teacher_id INTEGER REFERENCES users(id)
);

CREATE TABLE classes (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    teacher_id INTEGER REFERENCES users(id)
);

CREATE TABLE enrollments (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id),
    class_id   INTEGER REFERENCES classes(id)
);

CREATE TABLE notes (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id),
    class_id   INTEGER REFERENCES classes(id),
    grade      NUMERIC(4,1),
    comment    TEXT                    -- seed plaintext; web startup migrates to AES-GCM
);

-- admin (id 1)
INSERT INTO users (username,password,role,teacher_id) VALUES ('admin','admin123','admin',NULL);

-- teachers (ids 2..5)
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.turing','teach123','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.lovelace','teach123','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.hopper','teach123','teacher',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('prof.knuth','teach123','teacher',NULL);

-- students (ids 6..35)
INSERT INTO users (username,password,role,teacher_id) VALUES ('alice','alicepw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('bob','bobpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('carol','carolpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('dave','davepw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('eve','evepw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('frank','frankpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('grace','gracepw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('heidi','heidipw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('ivan','ivanpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('judy','judypw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('mallory','mallorypw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('niaj','niajpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('olivia','oliviapw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('peggy','peggypw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('quentin','quentinpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('rupert','rupertpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('sybil','sybilpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('trent','trentpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('ursula','ursulapw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('victor','victorpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('wendy','wendypw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('xavier','xavierpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('yvonne','yvonnepw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('zack','zackpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('nora','norapw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('liam','liampw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('mia','miapw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('noah','noahpw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('emma','emmapw','student',NULL);
INSERT INTO users (username,password,role,teacher_id) VALUES ('lucas','lucaspw','student',NULL);

-- classes (ids 1..4), teacher_id references users ids 2..5
INSERT INTO classes (name,teacher_id) VALUES ('Mathematics',2);
INSERT INTO classes (name,teacher_id) VALUES ('History',3);
INSERT INTO classes (name,teacher_id) VALUES ('Physics',4);
INSERT INTO classes (name,teacher_id) VALUES ('Computer Science',5);

-- enrollments + notes
INSERT INTO enrollments (student_id,class_id) VALUES (6,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (6,1,16.2,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (6,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (6,4,10.5,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (7,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (7,1,12.6,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (7,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (7,3,9.0,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (8,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (8,1,10.2,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (8,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (8,3,12.6,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (9,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (9,3,16.3,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (9,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (9,1,15.7,'Should ask more questions.');
INSERT INTO enrollments (student_id,class_id) VALUES (10,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (10,3,10.4,'Should ask more questions.');
INSERT INTO enrollments (student_id,class_id) VALUES (10,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (10,1,9.1,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (11,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (11,1,17.3,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (11,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (11,2,10.9,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (12,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (12,4,9.4,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (12,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (12,3,8.9,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (13,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (13,3,10.1,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (13,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (13,4,8.5,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (14,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (14,3,17.4,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (14,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (14,1,12.2,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (15,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (15,3,12.1,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (15,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (15,1,15.4,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (16,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (16,2,16.0,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (16,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (16,3,13.1,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (17,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (17,2,11.6,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (17,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (17,3,10.5,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (18,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (18,3,10.9,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (18,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (18,2,18.0,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (19,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (19,3,15.2,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (19,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (19,1,17.7,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (20,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (20,2,9.5,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (20,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (20,4,13.9,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (21,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (21,4,12.4,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (21,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (21,3,19.0,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (22,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (22,4,16.3,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (22,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (22,1,9.7,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (23,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (23,4,8.7,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (23,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (23,3,14.6,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (24,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (24,3,17.5,'Solid work, keep it up.');
INSERT INTO enrollments (student_id,class_id) VALUES (24,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (24,4,15.5,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (25,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (25,3,11.7,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (25,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (25,4,12.8,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (26,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (26,1,17.6,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (26,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (26,3,18.7,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (27,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (27,1,11.3,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (27,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (27,3,14.7,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (28,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (28,3,13.9,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (28,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (28,1,18.1,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (29,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (29,3,8.2,'Should ask more questions.');
INSERT INTO enrollments (student_id,class_id) VALUES (29,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (29,2,17.7,'Great improvement this term.');
INSERT INTO enrollments (student_id,class_id) VALUES (30,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (30,2,10.6,'Good teamwork.');
INSERT INTO enrollments (student_id,class_id) VALUES (30,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (30,1,18.4,'Needs to review chapter 3.');
INSERT INTO enrollments (student_id,class_id) VALUES (31,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (31,4,18.8,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (31,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (31,1,16.4,'Excellent participation in class.');
INSERT INTO enrollments (student_id,class_id) VALUES (32,4);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (32,4,9.8,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (32,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (32,3,17.6,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (33,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (33,2,16.3,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (33,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (33,3,15.8,'Very strong final exam.');
INSERT INTO enrollments (student_id,class_id) VALUES (34,3);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (34,3,17.9,'Missed two labs.');
INSERT INTO enrollments (student_id,class_id) VALUES (34,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (34,2,9.3,'Late submission, but good quality.');
INSERT INTO enrollments (student_id,class_id) VALUES (35,1);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (35,1,8.2,'Creative approach to the project.');
INSERT INTO enrollments (student_id,class_id) VALUES (35,2);
INSERT INTO notes (student_id,class_id,grade,comment) VALUES (35,2,10.5,'Late submission, but good quality.');
