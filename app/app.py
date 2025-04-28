from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/Kurs'  # Замените на свои данные
app.config['SECRET_KEY'] = 'your_secret_key'  # Секретный ключ для JWT
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

class User(db.Model):
    __tablename__ = 'users' 
    id = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(255), nullable=False)
    direction = db.Column(db.String(255), nullable=False)
    group_number = db.Column(db.String(50), nullable=False)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<User {self.login}>"

@app.route('/')
def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['login']
        password_input = request.form['password']

        user = User.query.filter_by(login=login_input).first()

        if not user or not bcrypt.check_password_hash(user.password, password_input):
            return jsonify({"msg": "Неверный логин или пароль"}), 401

        access_token = create_access_token(identity=user.id)
        session['user_id'] = user.id  # Сохраняем id пользователя в сессии

        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fio = request.form['fio']
        direction = request.form['direction']
        group_number = request.form['group_number']
        login = request.form['login']
        password = request.form['password']
        role = request.form['role']  # Получаем роль из формы

        # Хэшируем пароль
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Создаём нового пользователя
        new_user = User(fio=fio, direction=direction, group_number=group_number, login=login, password=hashed_password, role=role)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Удаляем пользователя из сессии
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
