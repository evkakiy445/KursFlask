from flask import Blueprint, render_template, session, redirect, url_for
from app.models import User, ElectiveCourse

student_courses_bp = Blueprint('student_courses', __name__, template_folder='templates')

@student_courses_bp.route('/student_courses')
def student_courses():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if user.role != 'Студент':
        return redirect(url_for('index'))

    # Извлекаем номер курса из группы
    group_number = user.group_number
    try:
        course_year = int(group_number[2])
    except (IndexError, ValueError):
        course_year = 1  # fallback по умолчанию

    # Каждый курс содержит 2 семестра: например, курс 1 → семестры 1 и 2
    semesters = [course_year * 2 - 1, course_year * 2]

    print("Группа:", group_number)
    print("Курс:", course_year)
    print("Семестры:", semesters)
    print("Направление:", user.direction_id)

    # Отбираем дисциплины по направлению и семестру
    elective_courses = ElectiveCourse.query.filter(
        ElectiveCourse.direction_id == user.direction_id,
        ElectiveCourse.semester.in_(semesters)
    ).all()

    return render_template(
        'index.html',
        user=user,
        elective_courses=elective_courses
    )
