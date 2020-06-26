
#importing required libraries and packages
from flask import render_template, request, flash, redirect, url_for, current_app
from blog import app, db, bcrypt, login_manager
from flask_login import login_user, login_required, current_user, logout_user
from .models import User, Post, Comment
import os
import secrets
from werkzeug.utils import secure_filename

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


def save_image(photo):
    hash_photo = secrets.token_urlsafe(10)
    _, file_extention = os.path.splitext(photo.filename)
    photo_name = hash_photo + file_extention
    file_path = os.path.join(current_app.root_path, 'static/images', photo_name)
    photo.save(file_path)
    return photo_name


#defining routes
@app.route('/', methods=['POST', 'GET'])
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/post/')
@app.route('/post/<int:post_id>/<string:slug>', methods=['GET', 'POST'])
def post(post_id, slug):
    post = Post.query.get_or_404(post_id)
    posts = Post.query.order_by(Post.id.desc()).all()
    comments = Comment.query.filter_by(post_id=post.id).all()
    post.views += 1
    db.session.commit()

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        comment = Comment(name=name, email=email, message=message, post_id=post.id)
        db.session.add(comment)
        post.comments += 1
        flash('Your comments has submitted', 'success')
        db.session.commit()
        return redirect(request.url)
    return render_template('image-post.html', post=post, posts=posts, comments=comments)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            flash("The user name already exist!", 'warning')
            return redirect(url_for('register'))
        email = User.query.filter_by(email=request.form.get('email')).first()
        if email:
            flash("The email id already exist!", 'warning')
            return redirect(url_for('register'))
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        reenter_password = request.form.get("reenter_password")
        if reenter_password != password:
            flash("Password do not matching. Please check again.", 'warning')
            return redirect(url_for('register'))
        password_has = bcrypt.generate_password_hash(password)
        users = User(name=name, username=username, email=email, password=password_has)
        db.session.add(users)
        db.session.commit()
        flash("Thank you for registration!", 'success')
        return redirect(url_for('dashboard'))

    return render_template('admin/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('dashboard'))
        flash('Wrong Password, Try again.', 'danger')
    return render_template('admin/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('admin/dashboard.html', posts=posts)


@app.route('/addpost', methods=['GET','POST'])
@login_required
def addpost():
    if request.method == "POST":
        title = request.form.get('title')
        body = request.form.get('content')
        photo = save_image(request.files.get('photo'))
        post = Post(title=title, body=body, image=photo, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been added!!!', 'success')
        return redirect('dashboard')
    return render_template('admin/addpost.html')


@app.route('/updatepost/<id>', methods=['POST', 'GET'])
@login_required
def updatepost(id):
    post = Post.query.get_or_404(id)
    if request.method == "POST":
        if request.files.get('photo'):
            try:
                os.unlink(os.path.join(current_app.root_path, 'static/images/'+post.image))
                post.image = save_image(request.files.get('photo'))
            except:
                post.image = save_image(request.files.get('photo'))
        post.title = request.form.get('title')
        post.body = request.form.get('content')
        db.session.commit()
        flash('Post Updated!!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('admin/updatepost.html', post=post)


@app.route('/delete/<id>', methods=['POST', 'GET'])
@login_required
def delete(id):
    post = Post.query.get_or_404(id)
    try:
        os.unlink(os.path.join(current_app.root_path, 'static/images/' + post.image))
        db.session.delete(post)
    except:
        db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted!!', 'success')
    return redirect(url_for('dashboard'))
