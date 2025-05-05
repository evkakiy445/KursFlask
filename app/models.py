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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    semester = db.Column(db.Integer)
    direction_id = db.Column(db.Integer, db.ForeignKey('direction.id'), nullable=False)