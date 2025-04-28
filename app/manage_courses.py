from flask import Blueprint, render_template, redirect, url_for, session
from .models import User

manage_courses_bp = Blueprint('manage_courses_bp', __name__)

@manage_courses_bp.route('/manage-courses')
def manage_courses():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user.role != 'Специалист дирекции':
        return redirect(url_for('index'))
    return render_template('manage_courses.html', user=user)
