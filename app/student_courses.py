from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import db, User, ElectiveCourse, StudentElectiveCourse, Settings

student_courses_bp = Blueprint('student_courses', __name__, template_folder='templates')

@student_courses_bp.route('/student_courses', methods=['GET', 'POST'])
def student_courses():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if user.role != 'Студент':
        return redirect(url_for('index'))

    group_number = user.group_number
    try:
        course_year = int(group_number[2])
    except (IndexError, ValueError):
        course_year = 1

    semesters = [course_year * 2 - 1, course_year * 2]

    elective_courses = ElectiveCourse.query.filter(
        ElectiveCourse.direction_id == user.direction_id,
        ElectiveCourse.semester.in_(semesters)
    ).all()

    course_pairs = [elective_courses[i:i+2] for i in range(0, len(elective_courses), 2)]

    chosen_courses = ElectiveCourse.query.join(StudentElectiveCourse).filter(
        StudentElectiveCourse.user_id == user.id
    ).all()
    chosen_course_ids = {course.id for course in chosen_courses}

    if request.method == 'POST':
        selected_ids = []
        for i, pair in enumerate(course_pairs):
            selected_id = request.form.get(f'pair_{i}')
            if not selected_id:
                flash(f"Пожалуйста, выберите дисциплину в паре {i + 1}.", "error")
                return redirect(url_for('student_courses.student_courses'))

            selected_ids.append(int(selected_id))

        # Удаляем предыдущие выборы
        StudentElectiveCourse.query.filter_by(user_id=user.id).delete()

        for selected_id in selected_ids:
            student_course = StudentElectiveCourse(user_id=user.id, elective_course_id=selected_id)
            db.session.add(student_course)

        db.session.commit()

        flash("Ваш выбор сохранён.")
        return redirect(url_for('student_courses.student_courses'))

    settings = Settings.query.first()
    is_enrollment_open = settings.is_enrollment_open if settings else False

    return render_template('choose_courses.html',
                           user=user,
                           course_pairs=list(enumerate(course_pairs)),
                           chosen_courses=chosen_courses,
                           chosen_course_ids=chosen_course_ids,
                           is_enrollment_open=is_enrollment_open)

