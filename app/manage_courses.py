import os
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from werkzeug.utils import secure_filename
from app.models import User, Direction, ElectiveCourse, db
import pandas as pd

manage_courses_bp = Blueprint('manage_courses_bp', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_excel_file(filepath):
    try:
        xls = pd.ExcelFile(filepath)

        sheet_name = None
        for name in xls.sheet_names:
            if 'уп' in name.lower():
                sheet_name = name
                break

        if not sheet_name:
            return None, "Не найден лист с учебным планом"

        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)

        # Поиск строки с направлением
        direction_row = None
        for i, row in df.iterrows():
            for cell in row:
                if isinstance(cell, str) and '09.03.02' in cell:
                    direction_row = row
                    break
            if direction_row is not None:
                break

        if direction_row is None:
            return None, "Не найдена информация о направлении"

        direction_info = direction_row[0]
        direction_code = '09.03.02'
        direction_name = direction_info.split('-')[-1].strip()

        elective_courses = []
        current_semester = None
        start_index = None

        # Поиск строки с "Дисциплины по выбору"
        for i, row in df.iterrows():
            if any(isinstance(cell, str) and 'дисциплины по выбору' in cell.lower() for cell in row):
                start_index = i + 1
                break

        if start_index is None:
            return None, "Не найдены 'Дисциплины по выбору' в файле"

        # Поиск текущего семестра (в предыдущих строках)
        for k in range(start_index - 1, max(start_index - 6, 0), -1):
            row = df.iloc[k]
            for cell in row:
                if isinstance(cell, str) and 'семестр' in cell.lower():
                    try:
                        current_semester = int(cell.split()[0])
                    except:
                        current_semester = None

        # Чтение дисциплин
        for j in range(start_index, len(df)):
            row = df.iloc[j]
            if row.isnull().all():
                break  # конец списка дисциплин

            # Поиск названия в первом непустом текстовом столбце
            course_name = None
            for cell in row:
                if isinstance(cell, str) and cell.strip():
                    course_name = cell.strip()
                    break

            if course_name and not any(x in course_name.lower() for x in ['дисциплины по выбору', 'семестр', 'курс']):
                elective_courses.append({
                    'name': course_name,
                    'semester': current_semester
                })

        return {
            'direction': {
                'code': direction_code,
                'name': direction_name
            },
            'elective_courses': elective_courses
        }, None

    except Exception as e:
        return None, f"Ошибка обработки файла: {str(e)}"


@manage_courses_bp.route('/manage-courses')
def manage_courses():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user.role != 'Специалист дирекции':
        return redirect(url_for('index'))

    directions = Direction.query.all()
    elective_courses = ElectiveCourse.query.all()

    return render_template('manage_courses.html',
                           user=user,
                           directions=directions,
                           elective_courses=elective_courses)

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

        result, error = process_excel_file(upload_path)

        if error:
            flash(f'Ошибка обработки файла: {error}', 'error')
            return redirect(url_for('manage_courses_bp.manage_courses'))

        direction = Direction.query.filter_by(code=result['direction']['code']).first()
        if not direction:
            direction = Direction(
                code=result['direction']['code'],
                name=result['direction']['name']
            )
            db.session.add(direction)
            db.session.commit()

        for course in result['elective_courses']:
            existing_course = ElectiveCourse.query.filter_by(
                name=course['name'],
                direction_id=direction.id
            ).first()

            if not existing_course:
                elective_course = ElectiveCourse(
                    name=course['name'],
                    semester=course['semester'],
                    direction_id=direction.id
                )
                db.session.add(elective_course)

        db.session.commit()

        flash('Файл успешно загружен и обработан', 'success')
        return redirect(url_for('manage_courses_bp.manage_courses'))
    else:
        flash('Недопустимый формат файла. Разрешены только .xls и .xlsx', 'error')
        return redirect(url_for('manage_courses_bp.manage_courses'))
