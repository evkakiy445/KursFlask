from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(255), nullable=False)
    direction_id = db.Column(db.Integer, db.ForeignKey('direction.id'), nullable=False)  # внешний ключ
    group_number = db.Column(db.String(50), nullable=False)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    direction = db.relationship('Direction', backref=db.backref('users', lazy=True))  # связь с таблицей Direction

    def __repr__(self):
        return f"<User {self.login}>"

class Direction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    elective_courses = db.relationship('ElectiveCourse', backref='direction', lazy=True)

class ElectiveCourse(db.Model):
    __tablename__ = 'elective_course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    semester = db.Column(db.Integer)
    direction_id = db.Column(db.Integer, db.ForeignKey('direction.id'), nullable=False)

class StudentElectiveCourse(db.Model):
    __tablename__ = 'student_elective_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    elective_course_id = db.Column(db.Integer, db.ForeignKey('elective_course.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('elective_courses', lazy=True))
    elective_course = db.relationship('ElectiveCourse', backref=db.backref('students', lazy=True, cascade='all, delete'))

    def __repr__(self):
        return f"<StudentElectiveCourse user_id={self.user_id}, elective_course_id={self.elective_course_id}>"


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_enrollment_open = db.Column(db.Boolean, default=True)
