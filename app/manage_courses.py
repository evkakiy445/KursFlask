import os
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from werkzeug.utils import secure_filename
from app.models import User, Direction, ElectiveCourse, Settings, db
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

        direction_code = None
        direction_name = None
        
        for i, row in df.iterrows():
            for cell in row:
                if isinstance(cell, str) and '09.03.02' in cell:
                    parts = cell.split('-')
                    if len(parts) > 1:
                        direction_code = '09.03.02'
                        direction_name = parts[-1].strip()
                        break
            if direction_code:
                break

        if not direction_code:
            return None, "Не найдена информация о направлении"

        elective_courses = []
        
        for i, row in df.iterrows():
            for j, cell in enumerate(row):
                if isinstance(cell, str) and 'дисциплины по выбору' in cell.lower():
                    semester = None
                    for k in range(j, len(row)):
                        if isinstance(row[k], (int, float)) and 1 <= row[k] <= 8:
                            semester = int(row[k])
                            break
                    
                    if semester:
                        for k in range(i+1, min(i+20, len(df))):
                            course_name = df.iloc[k, j]
                            if isinstance(course_name, str) and course_name.strip() and not any(
                                x in course_name.lower() for x in ['дисциплины по выбору', 'семестр', 'курс']
                            ):
                                elective_courses.append({
                                    'name': course_name.strip(),
                                    'semester': semester
                                })
                            elif pd.isna(course_name) or (isinstance(course_name, str) and not course_name.strip()) or not isinstance(course_name, str):
                                break

        for sheet in xls.sheet_names:
            if any(x in sheet.lower() for x in ['курс', 'course']):
                sheet_df = pd.read_excel(filepath, sheet_name=sheet, header=None)
                
                semester = None
                if '1' in sheet:
                    semester = 1 if 'семестр' not in sheet.lower() else None
                elif '2' in sheet:
                    semester = 3 if 'семестр' not in sheet.lower() else None
                elif '3' in sheet:
                    semester = 5 if 'семестр' not in sheet.lower() else None
                elif '4' in sheet:
                    semester = 7 if 'семестр' not in sheet.lower() else None
                
                if not semester:
                    continue
                
                for i, row in sheet_df.iterrows():
                    for j, cell in enumerate(row):
                        if isinstance(cell, str) and 'дисциплины по выбору' in cell.lower():
                            for k in range(i+1, min(i+20, len(sheet_df))):
                                course_name = sheet_df.iloc[k, j]
                                if isinstance(course_name, str) and course_name.strip() and not any(
                                    x in course_name.lower() for x in ['дисциплины по выбору', 'семестр', 'курс']
                                ):
                                    elective_courses.append({
                                        'name': course_name.strip(),
                                        'semester': semester
                                    })
                                elif pd.isna(course_name) or (isinstance(course_name, str) and not course_name.strip()) or not isinstance(course_name, str):
                                    break

        seen = set()
        unique_courses = []
        for course in elective_courses:
            key = (course['name'], course['semester'])
            if key not in seen:
                seen.add(key)
                unique_courses.append(course)

        return {
            'direction': {
                'code': direction_code,
                'name': direction_name
            },
            'elective_courses': unique_courses
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
    settings = Settings.query.first()
    return render_template('manage_courses.html',
                       user=user,
                       directions=directions,
                       elective_courses=elective_courses,
                       settings=settings)

@manage_courses_bp.route('/toggle-enrollment', methods=['POST'])
def toggle_enrollment():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user.role != 'Специалист дирекции':
        return redirect(url_for('index'))

    settings = Settings.query.first()
    if not settings:
        settings = Settings(is_enrollment_open=True)
        db.session.add(settings)
    else:
        settings.is_enrollment_open = not settings.is_enrollment_open

    db.session.commit()
    flash(f"Запись на дисциплины {'открыта' if settings.is_enrollment_open else 'закрыта'}", "success")
    return redirect(url_for('manage_courses_bp.manage_courses'))


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