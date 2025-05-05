from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from app.models import db, User
from app.manage_courses import manage_courses_bp
from app.student_courses import student_courses_bp
from app.models import Direction

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

    @app.route('/')
    def index():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        user = User.query.get(user_id)
        if user.role == 'Специалист дирекции':
            return redirect(url_for('director_dashboard'))
        else:
            return render_template('layout.html', user=user)

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
            else:
                return redirect(url_for('index'))

        return render_template('login.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            fio = request.form['fio']
            direction_id = request.form['direction']
            group_number = request.form['group_number']
            login = request.form['login']
            password = request.form['password']
            role = request.form['role'].strip().capitalize()

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

    @app.route('/reports')
    def reports():
        return render_template('reports.html')
        
    @app.route('/manage_students_courses')
    def manage_students_courses():
        return render_template('manage_students_courses.html')

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
