import os
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from werkzeug.utils import secure_filename
from app.models import User

manage_courses_bp = Blueprint('manage_courses_bp', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@manage_courses_bp.route('/manage-courses')
def manage_courses():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user.role != 'Специалист дирекции':
        return redirect(url_for('index'))
    return render_template('manage_courses.html', user=user)

@manage_courses_bp.route('/upload-plan', methods=['POST'])
def upload_plan():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user.role != 'Специалист дирекции':
        return redirect(url_for('index'))

    if 'plan_file' not in request.files:
        flash('Файл не был загружен', 'error')
        return redirect(url_for('manage_courses_bp.manage_courses'))

    file = request.files['plan_file']

    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('manage_courses_bp.manage_courses'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(UPLOAD_FOLDER, filename)

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(upload_path)

        flash('Файл успешно загружен', 'success')
        return redirect(url_for('manage_courses_bp.manage_courses'))
    else:
        flash('Недопустимый формат файла. Разрешены только .xls и .xlsx', 'error')
        return redirect(url_for('manage_courses_bp.manage_courses'))
