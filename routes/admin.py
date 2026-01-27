"""Admin routes for bookmark management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models import Bookmark, Group, User

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin access."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('frontend.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/bookmarks')
@admin_required
def bookmarks():
    """Bookmark management page."""
    bookmarks = Bookmark.query.order_by(Bookmark.order).all()
    groups = Group.query.order_by(Group.order).all()
    users = User.query.all()
    return render_template('admin/bookmarks.html',
                         bookmarks=bookmarks,
                         groups=groups,
                         users=users)


@admin.route('/bookmarks/create', methods=['POST'])
@admin_required
def create_bookmark():
    """Create a new bookmark."""
    try:
        title = request.form.get('title')
        url = request.form.get('url')
        user_id = request.form.get('user_id')
        group_id = request.form.get('group_id')

        # Get max order
        max_order = db.session.query(db.func.max(Bookmark.order)).scalar() or 0

        bookmark = Bookmark(
            title=title,
            url=url,
            user_id=user_id,
            group_id=group_id if group_id else None,
            order=max_order + 1
        )
        db.session.add(bookmark)
        db.session.commit()

        flash('Bookmark created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating bookmark: {str(e)}', 'danger')

    return redirect(url_for('admin.bookmarks'))


@admin.route('/bookmarks/<int:bookmark_id>/update', methods=['POST'])
@admin_required
def update_bookmark(bookmark_id):
    """Update an existing bookmark."""
    bookmark = Bookmark.query.get_or_404(bookmark_id)

    try:
        bookmark.title = request.form.get('title')
        bookmark.url = request.form.get('url')
        group_id = request.form.get('group_id')
        bookmark.group_id = group_id if group_id else None

        db.session.commit()
        flash('Bookmark updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating bookmark: {str(e)}', 'danger')

    return redirect(url_for('admin.bookmarks'))


@admin.route('/bookmarks/<int:bookmark_id>/delete', methods=['POST'])
@admin_required
def delete_bookmark(bookmark_id):
    """Delete a bookmark."""
    bookmark = Bookmark.query.get_or_404(bookmark_id)

    try:
        db.session.delete(bookmark)
        db.session.commit()
        flash('Bookmark deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting bookmark: {str(e)}', 'danger')

    return redirect(url_for('admin.bookmarks'))


@admin.route('/bookmarks/reorder', methods=['POST'])
@admin_required
def reorder_bookmarks():
    """Reorder bookmarks via drag and drop."""
    try:
        order = request.json.get('order', [])

        for index, bookmark_id in enumerate(order, start=1):
            bookmark = Bookmark.query.get(bookmark_id)
            if bookmark:
                bookmark.order = index

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
