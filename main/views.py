# -*- coding: utf-8 -*-

"""

    main.views
    ~~~~~~~~~~

    This module implements all the basic views of Subrosa

    :copyright: (c) 2014 by Konrad Wasowicz
    :license: BSD, see LICENSE for more details


"""

from main import app, db
from flask import render_template, redirect, flash, request, g, abort, session, url_for, send_from_directory
from .models import User, Articles, UserImages
from .helpers import Pagination, login_required,\
process_image, make_external, redirect_url, handle_errors,\
dynamic_content
from werkzeug import secure_filename
import os
from datetime import datetime
from werkzeug.contrib.atom import AtomFeed




@app.before_request
def load_vars():
    g.title = app.config["TITLE"]
    g.prev = redirect_url()


@app.route("/", defaults={"page": 1})
@app.route("/<int:page>")
def index(page):
    pages_per_page = app.config["ARTICLES_PER_PAGE"]
    articles = Articles\
               .get_articles_by_date()\
               .paginate(page, pages_per_page)
    if not articles.items and page != 1:
        abort(404)
    return render_template("index.html", articles = articles)

@app.route("/index", methods = ["GET"])
def redirect_index():
    return redirect(url_for("index"))

@app.route("/admin", methods = ["GET", "POST"] )
def admin_login():
    # Check if any users exist
    user_check = User.query.all()
    # If not redirect to account creation screen
    if not user_check:
        return redirect(url_for("create_account"))
    if "user" in session:
        return redirect(url_for("account", username = session["user"]))

    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username = username).first()
        if not user:
            error = "Incorrect Credentials"
            return render_template("login.html", error = error)
        else:
            if not user.check_password(password):
                error = "Incorrect Credentials"
                return render_template("login.html", error = error)
            else:
                session["user"] = user.username
                return redirect(url_for("account", username = user.username))
    return render_template("login.html", error = error)

@app.route("/create_account", methods = ["POST", "GET"])
def create_account():
    """
    View for creating user account
    - Checks if no users have been created - if yes redirect
    - Gets Credentials from the form
    - Writes data to db
    - Creates user directory in /uploads
    - Logs user in

    """
    error = None
    # check if no users created yet
    user_check = User.query.all()
    if not user_check:
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            real_name = request.form.get("real_name", None)
            if username and email and password:
                new_user = User(username = username, email = email,\
                                real_name = real_name, password = password)
                try:
                    db.session.add(new_user)
                    db.session.commit()
                except IOError, e:
                    db.session.rollback()
                    error = "Could not write to database, check if\
                            you have proper access\n or double check configuration options"
                    handle_errors(error)
                    return render_template("create_account.html", error = error)
                try:
                    os.mkdir(app.config["UPLOAD_FOLDER"] + username, 0755)
                    os.mkdir(app.config["UPLOAD_FOLDER"] + username + "/thumbnails", 0755)
                    os.mkdir(app.config["UPLOAD_FOLDER"] + username + "/showcase", 0755)
                except IOError, e:
                    error = "Could not create user directories, check\
                            if you have proper credentials"
                    hendle_errors(error)
                    return render_template("create_account.html", error = error)
                session["user"] = username
                flash("Account created")
                return redirect(url_for("account", username = username))
            else:
                error = "All fields are required"
                return render_template("create_account.html", error = error)
        else:
            return render_template("create_account.html")
    else:
        return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    if "user" in session:
        session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/account/<username>", methods = ["GET","POST"])
@login_required
def account(username):
    if username is None:
        return redirect("/admin")
    user = User.query.filter_by(username = username).first()
    user_articles = Articles.query\
                    .filter_by(author = user)\
                    .order_by(Articles.date_created.desc())\
                    .all()
    return render_template("dashboard.html",user = user, articles = user_articles)


@app.route("/create_article", methods = ["GET", "POST"])
@login_required
def create_article():
    error = None
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        user = User.query\
               .filter_by(username = session["user"])\
               .first()
        # if body and title exists
        if not title or not body:
            error = "Article can\'t have empty title or body"
            return render_template("new_article.html", error = error, title=title, body=body)
        # if title is unique
        article_check = Articles.query.filter_by(title = title).first()
        if article_check:
            error = "Entry with that title already exists, choose a new one.."
            return render_template("new_article.html", error = error, title = title, body = body)
        else:
            article = Articles(title = title, draft = True, author = user, body = body)
            db.session.add(article)
            try:
                db.session.commit()
                flash("Article created")
                return redirect(url_for("index"))
            except Exception, e:
                if app.config.debug:
                    error = "Error occured when writing to database... Try again"
                    handle_errors(error)
                    return render_template("new_article.html",  title = title, body = body , error = error)
    else:
        return render_template("new_article.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_article(id):
    article = Articles.query.get_or_404(id)
    error = None

    if article.author.username != session["user"]:
       flash("You can\'t edit other people\'s articles")
       return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        if not title or not body:
            error = "Article can\'t have empty title or body"
            return render_template("edit_article.html", error = error, article = article)

        article_check = Articles.query.filter_by(title = title).first()

        if article_check and article_check.id != article.id:
            error = "Article with this title already exists, please choose another"
            return render_template("edit_article.html", error = error, article = article )
        else:
            article.title = title
            article.body = body
            article.date_updated = datetime.utcnow()
            db.session.add(article)
            try:
                db.session.commit()
                return redirect(url_for("account", username = session["user"]))
            except Exception, e:
                db.session.rollback()
                error = "Error writing to database"
                handle_errors(error)
                return render_template("edit_article.html", error = error, article = article )
    else:
        return render_template("edit_article.html", article = article)

@app.route("/article/<int:id>")
def article_view(id):
    article = Articles.query.get_or_404(id)
    return render_template("article_view.html", article = article)

@app.route("/delete_article/<int:id>")
@login_required
def delete_article(id):
    article = Articles.query.get_or_404(id)
    if article.author.username != session["user"]:
        flash("You can\'t delete other people\'s posts")
        return redirect(url_for("index"))
    else:
        db.session.delete(article)
        db.session.commit()
        flash("Article has been deleted")
        return redirect(url_for("account", username = session["user"]))

@app.route("/publish_article/<int:id>")
@login_required
def publish_article(id):
    article = Articles.query.get_or_404(id)
    if article.author.username != session["user"]:
        flash("You can\'t publish other\'s peoples posts")
        return redirect(url_for("index"))
    else:
        # add except here
        article.draft = False
        db.session.add(article)
        db.session.commit()
        flash("Article has been published")
        return redirect(url_for("account", username = session["user"]))


@app.route("/upload_image", methods = ["GET", "POST"])
@login_required
@dynamic_content
def upload_image():
    # Refactor this mess
    error = None
    if request.method == "POST":
        image = request.files["image"]
        gallery_include = request.form.get("gallery_include", False)
        if not image:
            error = "No image chosen"
            return render_template("upload_image.html", error = error)
        if os.path.splitext(image.filename)[1][1:] not in app.config["ALLOWED_FILENAMES"]:
            error = "Allowed extensions are %r" % (", ".join(app.config["ALLOWED_FILENAMES"]))
            return render_template("upload_image.html", error = error)
        # add checkbox functionality
        filename = secure_filename(request.form.get("image-name"))\
                                  or secure_filename(image.filename)
        # add gallery functionality
        try:
            image_filename, thumb_filename, show_filename = process_image(image = image, filename = filename , username = session["user"])
            try:
                user = User.query.filter_by(username = session["user"]).first()
                user_image = UserImages(filename = image_filename, thumbnail = thumb_filename, showcase = show_filename, gallery = gallery_include, owner = user)
                db.session.add(user_image)
                db.session.commit()
                return redirect(url_for("user_images", username = session["user"]))
            except Exception, e:
                error = "Error writing to database"
                handle_errors(error)
                return render_template("upload_image.html", error = error)
        except Exception, e:
            error = "Error occured while processing the image"
            handle_errors(error)
            return render_template("upload_image.html", error = error)
    else:
        return render_template("upload_image.html")

@app.route("/images/<username>", defaults={"page": 1})
@app.route("/images/<username>/<int:page>")
@login_required
@dynamic_content
def user_images(username, page):
    images = UserImages.query.join(User).paginate(page, 9)
    url_path = request.url_root +"uploads/"
    if not images.items and page != 1:
        abort(404)
    return render_template("user_images.html", images = images, url_path = url_path)

@app.route("/delete_image/<int:id>")
@login_required
@dynamic_content
def delete_image(id):
    image = UserImages.query.get(id)
    # prevent from deleting images by people other by the owner
    if image.owner.username != session["user"]:
        flash("Don't try to delete other\'s dude\'s pictures...dude")
        return redirect(url_for("index"))
    else:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], session["user"], image.filename))
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], session["user"],"thumbnails", image.thumbnail))
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], session["user"], "showcase", image.showcase))
        except IOError, e:
            flash("Can\'t delete files from disk")
            return redirect(url_for("index"))
        try:
            db.session.delete(image)
            db.session.commit()
        except IOError, e:
            db.session.rollback()
            error = "Error occured when writing to database"
            handle_errors(error)
            flash(error)
            return redirect(url_for("index"))
        return redirect(url_for("user_images", username = session["user"]))


# probably needs auth
@app.route("/image_details/<int:id>")
@dynamic_content
def image_details(id):
    image = UserImages.query.get_or_404(id)
    path = request.url_root
    return render_template("image_details.html",path = path, image = image)


@app.route("/recent.atom")
def recent_feeds():
    """
    Generates Atom feeds
    Snippet created by Armin Ronacher
    """
    feed = AtomFeed("Recent Posts", 
        feed_url = request.url, url = request.url_root)
    articles = Articles.query\
               .order_by(Articles.date_created.desc())\
               .limit(15)\
               .all()

    for article in articles:
        feed.add(article.title, unicode(article.body)[:320],
            content_type = "html",
            author = article.author,
            updated = article.date_updated,
            url = make_external(article.id),
            published = article.date_created
            )

    return feed.get_response()

@app.route("/uploads/<path:filename>")
@dynamic_content
def send_image(filename):
    """
    Allows sending images from upload folder
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.template_filter()
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.utcnow()
    diff = now - dt
    
    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )
    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)
    return default

@app.errorhandler(404)
def http_not_found(err):
    return render_template("error.html"), 404

