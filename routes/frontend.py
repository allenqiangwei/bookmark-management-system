"""Frontend routes for displaying bookmarks."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import Bookmark, Group

frontend = Blueprint('frontend', __name__)


@frontend.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login."""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.dashboard'))
    return redirect(url_for('auth.login'))


@frontend.route('/dashboard')
@login_required
def dashboard():
    """Display user's bookmarks organized by groups."""
    # Get all groups for the current user, ordered by order field
    groups = Group.query.filter_by(user_id=current_user.id).order_by(Group.order).all()

    # Get bookmarks for each group
    grouped_bookmarks = {}
    for group in groups:
        bookmarks = Bookmark.query.filter_by(
            user_id=current_user.id,
            group_id=group.id
        ).order_by(Bookmark.order).all()
        grouped_bookmarks[group.id] = bookmarks

    # Get ungrouped bookmarks
    ungrouped = Bookmark.query.filter_by(
        user_id=current_user.id,
        group_id=None
    ).order_by(Bookmark.order).all()

    return render_template(
        'dashboard.html',
        groups=groups,
        grouped_bookmarks=grouped_bookmarks,
        ungrouped=ungrouped
    )
