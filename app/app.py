from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from app.models import db, User, ElectiveCourse, StudentElectiveCourse, Settings
from app.manage_courses import manage_courses_bp
from app.student_courses import student_courses_bp
from app.models import Direction
from app.reports import reports_bp 
from app.models import db
from sqlalchemy import text
def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/Kurs'
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)

    app.register_blueprint(manage_courses_bp)
    app.register_blueprint(student_courses_bp)
    app.register_blueprint(reports_bp)

    @app.route('/')
    def index():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        user = User.query.get(user_id)
        if user.role == 'Специалист дирекции':
            return redirect(url_for('director_dashboard'))
        else:
            return render_template('index.html', user=user)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            login_input = request.form['login']
            password_input = request.form['password']

            user = User.query.filter_by(login=login_input).first()

            if not user or not bcrypt.check_password_hash(user.password, password_input):
                return render_template('login.html', error="Неверный логин или пароль")

            session['user_id'] = user.id

            print(f"Роль пользователя: {user.role}")

            if user.role == 'Специалист дирекции':
                return redirect(url_for('director_dashboard'))
            elif user.role.lower() == 'студент':
                return redirect(url_for('student_courses.student_courses'))
            elif user.role.lower() == 'преподаватель':
                return redirect(url_for('reports_bp.generate_reports'))
            else:
                return redirect(url_for('index'))

        return render_template('login.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            fio = request.form['fio']
            role = request.form['role'].strip().capitalize()
            login = request.form['login']
            password = request.form['password']

            # Проверка наличия полей для студента
            if role == 'Студент':
                direction_id = request.form.get('direction')  # Используем get(), чтобы избежать ошибки
                group_number = request.form.get('group_number')

                # Если одно из полей пустое
                if not direction_id or not group_number:
                    return render_template('register.html', directions=Direction.query.all(), error="Направление и номер группы обязательны для студента")
            else:
                direction_id = None
                group_number = None

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            new_user = User(
                fio=fio,
                direction_id=direction_id,
                group_number=group_number,
                login=login,
                password=hashed_password,
                role=role
            )

            db.session.add(new_user)
            db.session.commit()

            print(f"Роль при регистрации: {role}")

            return redirect(url_for('login'))

        directions = Direction.query.all()
        return render_template('register.html', directions=directions)



    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('login'))
        
    @app.route('/manage_students_courses', methods=['GET', 'POST'])
    def manage_students_courses():
        if request.method == 'POST':
            student_id = request.form.get('student')
            course_id = request.form.get('course')
            action = request.form.get('action')

            if student_id and course_id:
                if action == 'assign':
                    insert_query = text("""
                        INSERT INTO student_elective_courses (user_id, elective_course_id)
                        VALUES (:student_id, :course_id)
                    """)
                    db.session.execute(insert_query, {'student_id': student_id, 'course_id': course_id})
                elif action == 'remove':
                    delete_query = text("""
                        DELETE FROM student_elective_courses
                        WHERE user_id = :student_id AND elective_course_id = :course_id
                    """)
                    db.session.execute(delete_query, {'student_id': student_id, 'course_id': course_id})

                db.session.commit()

        # Получаем все данные для отображения
        student_query = text("SELECT id, fio FROM users WHERE role = 'Студент'")
        students = db.session.execute(student_query).fetchall()

        course_query = text("SELECT id, name FROM elective_course")
        courses = db.session.execute(course_query).fetchall()

        assigned_query = text("""
            SELECT users.fio, elective_course.name AS course_name
            FROM student_elective_courses
            JOIN users ON student_elective_courses.user_id = users.id
            JOIN elective_course ON student_elective_courses.elective_course_id = elective_course.id
            ORDER BY users.fio;
        """)
        assigned = db.session.execute(assigned_query).fetchall()

        return render_template(
            'manage_students_courses.html',
            students=students,
            courses=courses,
            assigned=assigned
        )

    @app.route('/director_dashboard')
    def director_dashboard():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        user = User.query.get(user_id)
        return render_template('director_dashboard.html', user=user)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
