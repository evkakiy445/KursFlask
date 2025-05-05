from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import db, User, ElectiveCourse, StudentElectiveCourse

student_courses_bp = Blueprint('student_courses', __name__, template_folder='templates')

@student_courses_bp.route('/student_courses', methods=['GET', 'POST'])
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

    # Отбираем дисциплины по направлению и семестру
    elective_courses = ElectiveCourse.query.filter(
        ElectiveCourse.direction_id == user.direction_id,
        ElectiveCourse.semester.in_(semesters)
    ).all()

    # Разбиваем дисциплины на пары
    course_pairs = [elective_courses[i:i+2] for i in range(0, len(elective_courses), 2)]

    if request.method == 'POST':
        selected_ids = []
        # Проверка, что студент выбрал дисциплину из каждой пары
        for i, pair in enumerate(course_pairs):
            selected_id = request.form.get(f'pair_{i}')
            if not selected_id:
                flash(f"Пожалуйста, выберите дисциплину в паре {i + 1}.", "error")
                return redirect(url_for('student_courses.student_courses'))

            selected_ids.append(int(selected_id))

        # Сохраняем выбор пользователя в базу данных
        for selected_id in selected_ids:
            course = ElectiveCourse.query.get(selected_id)
            if course:
                # Предположим, что есть таблица для связи студентов и их дисциплин
                student_course = StudentElectiveCourse(user_id=user.id, elective_course_id=course.id)
                db.session.add(student_course)

        db.session.commit()

        flash("Ваш выбор сохранён.")
        return redirect(url_for('student_courses.student_courses'))

    return render_template(
        'choose_courses.html',
        user=user,
        course_pairs=list(enumerate(course_pairs))
    )
