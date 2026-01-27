"""Admin routes for bookmark management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.exc import IntegrityError
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


@admin.route('/groups')
@login_required
def groups():
    """分组管理页面"""
    try:
        groups = Group.query.filter_by(user_id=current_user.id).order_by(Group.order).all()

        # 为每个分组统计书签数量
        groups_with_counts = []
        for group in groups:
            count = Bookmark.query.filter_by(group_id=group.id).count()
            groups_with_counts.append({
                'group': group,
                'bookmark_count': count
            })

        return render_template('admin/groups.html', groups_with_counts=groups_with_counts)
    except Exception as e:
        flash(f'加载分组列表时发生错误: {str(e)}', 'danger')
        return render_template('admin/groups.html', groups_with_counts=[])


@admin.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    """创建分组"""
    name = request.form.get('name')

    if not name or not name.strip():
        flash('分组名称不能为空', 'danger')
        return redirect(url_for('admin.groups'))

    # 获取最大order值
    max_order = db.session.query(db.func.max(Group.order)).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    group = Group(
        user_id=current_user.id,
        name=name.strip(),
        order=max_order + 1
    )

    db.session.add(group)

    try:
        db.session.commit()
        flash('分组创建成功', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('该分组名称已存在', 'danger')
        return redirect(url_for('admin.groups'))

    return redirect(url_for('admin.groups'))


@admin.route('/groups/<int:group_id>/update', methods=['POST'])
@login_required
def update_group(group_id):
    """更新分组"""
    group = Group.query.filter_by(id=group_id, user_id=current_user.id).first_or_404()

    name = request.form.get('name')
    if not name or not name.strip():
        flash('分组名称不能为空', 'danger')
        return redirect(url_for('admin.groups'))

    group.name = name.strip()

    try:
        db.session.commit()
        flash('分组更新成功', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('该分组名称已存在', 'danger')
        return redirect(url_for('admin.groups'))

    return redirect(url_for('admin.groups'))


@admin.route('/groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    """删除分组"""
    group = Group.query.filter_by(id=group_id, user_id=current_user.id).first_or_404()

    try:
        # 删除分组，书签会自动变为未分组（ON DELETE SET NULL）
        db.session.delete(group)
        db.session.commit()
        flash('分组删除成功，原书签已移至未分类', 'success')
    except Exception as e:
        db.session.rollback()
        flash('删除分组失败', 'danger')

    return redirect(url_for('admin.groups'))


@admin.route('/groups/reorder', methods=['POST'])
@login_required
def reorder_groups():
    """重新排序分组"""
    try:
        data = request.get_json()
        group_orders = data.get('groups', [])

        for item in group_orders:
            group = Group.query.filter_by(
                id=item['id'],
                user_id=current_user.id
            ).first()

            if group:
                group.order = item['order']

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin.route('/users')
@admin_required
def users():
    """用户管理页面"""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    """创建用户"""
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'

    if not username or not password:
        flash('用户名和密码不能为空', 'danger')
        return redirect(url_for('admin.users'))

    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('用户名已存在', 'danger')
        return redirect(url_for('admin.users'))

    user = User(username=username, is_admin=is_admin)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash(f'用户 {username} 创建成功', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    """重置用户密码"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('password')

    if not new_password:
        flash('新密码不能为空', 'danger')
        return redirect(url_for('admin.users'))

    user.set_password(new_password)
    db.session.commit()

    flash(f'用户 {user.username} 的密码已重置', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)

    # 防止删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录的用户', 'danger')
        return redirect(url_for('admin.users'))

    # 确保至少保留一个管理员
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('至少需要保留一个管理员账号', 'danger')
            return redirect(url_for('admin.users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'用户 {username} 已删除', 'success')
    return redirect(url_for('admin.users'))
