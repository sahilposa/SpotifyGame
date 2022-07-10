"""Main Server Page"""
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals
# pylint: disable=no-member
# pylint: disable=consider-using-f-string
from json.encoder import INFINITY
import os
from dotenv import find_dotenv, load_dotenv
import flask
from flask_login import LoginManager, UserMixin, current_user
from flask_login import login_user, login_required, logout_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import api


load_dotenv(find_dotenv())

app = flask.Flask(__name__, template_folder="templates")

bp = flask.Blueprint(
    "bp",
    __name__,
    template_folder="./static/react",
)

app.config["SECRET_KEY"] = "I have a secret key, wizard!"
# Point SQLAlchemy to your Heroku database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL").replace(
    "://", "ql://", 1
)
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "app.login"
login_manager.init_app(app)

genre = ["rock"]


@login_manager.user_loader
def load_user(user_id):
    """This function is used to load user"""
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """This class is used to create User database"""

    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    @property
    def password(self):
        """defines password"""
        raise AttributeError("password is not a readable attribute!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Function to verify password"""
        return check_password_hash(self.password_hash, password)

    # Create A String
    def __repr__(self):
        return "<Name %r>" % self.name


class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False, unique=False)
    username = db.Column(db.String(50), nullable=False, unique=False)


db.create_all()


@app.route("/")
def start():
    """This function is called on landing page to sign up"""
    value = 0
    page = 0
    if "page" in flask.session:
        page = flask.session["page"]
    if "user_exists" in flask.session:
        if flask.session["user_exists"]:
            value = 1
    return flask.render_template("signup.html", value=value, page=page)


@app.route("/signUpPage", methods=["GET", "POST"])
def sign():
    """This function is called on signUpPage to store the form data"""
    # code to validate and add user to database goes here

    username = flask.request.form.get("username")
    password_hash = flask.request.form.get("password_hash")
    # if this returns a user, then the username already exists in database
    user = User.query.filter_by(username=username).first()

    if user:
        # if a user is found, we want to redirect back to signup page so user can try again
        flask.session["user_exists"] = True
        flask.session["page"] = 1
        return flask.redirect(flask.url_for("start"))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(
        username=username, password_hash=generate_password_hash(password_hash)
    )

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return flask.render_template("login.html")


# login funtionality
@app.route("/loginPage", methods=["GET", "POST"])
def login():
    """This function is used to login the user"""
    if flask.request.method == "POST":
        data = flask.request.form  # gets username and password inputs
        query = db.session.query(User.id).filter(
            User.username == data["username"]
        )  # get user name from database
        # checks to see if User is in table
        in_table = db.session.query(query.exists()).scalar()

        if in_table:  # if in table User user is registered
            user = User.query.filter_by(username=data["username"]).first()

            # verifying password
            if check_password_hash(user.password_hash, data["password"]):
                login_user(user)
                return flask.redirect(
                    flask.url_for("profile")
                )  # login user and redirect to main page
            else:
                flask.flash("Wrong password, please try again.")
        else:
            flask.flash("Username is invalid.")
            return flask.redirect(flask.url_for("login"))

    return flask.render_template("login.html")


# profile page: temporary until connect to react
@app.route("/profilePage", methods=["GET", "POST"])
@login_required
def profile():
    """This function is used for users to view profile"""
    user_scores = Leaderboard.query.filter_by(username=current_user.username).all()
    len_user_scores = len(user_scores)
    return flask.render_template(
        "profile.html",
        username=current_user.username,
        user_scores=user_scores,
        len_user_scores=len_user_scores,
    )


@app.route("/logout")
@login_required
def logout():
    """This function is used to logout the user"""
    logout_user()
    return flask.redirect(flask.url_for("login"))


@app.route("/choosegenre", methods=["POST", "GET"])
@login_required
def choose_genre():
    """Function to set genre"""
    genres = ["    ", "rock", "pop", "folk", "country", "metal", "classical", "jazz"]
    if flask.request.method == "POST":
        genre[0] = flask.request.form["genres"]
        return flask.redirect(flask.url_for("choose_genre"))
    return flask.render_template("game.html", genres=genres)


@login_required
@bp.route("/gamepage", methods=["POST", "GET"])
def gamepage():
    """Function to direct to React page"""
    return flask.render_template("index.html")


@bp.route("/leaderboard", methods=["POST", "GET"])
@login_required
def leaderboard():
    scored = ""
    if flask.request.method == "POST":
        scored = flask.request.form.get("score", type=int)
        scores = Leaderboard(score=scored, username=current_user.username)
        db.session.add(scores)
        db.session.commit()

    allscores = Leaderboard.query.order_by(Leaderboard.score.desc())
    lensco = Leaderboard.query.all()
    len_allscores = len(lensco)
    return flask.render_template(
        "leaderboard.html",
        score=scored,
        allscores=allscores,
        len_allscores=len_allscores,
    )


@login_required
@bp.route("/getsongs", methods=["POST", "GET"])
def get_songs():
    """From genre, gets song data and returns to react"""
    urls = []
    names = []
    images = []
    artists = []
    print(genre)
    if genre[0] == "rock":
        uris = api.search_genre("rock")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)
    elif genre[0] == "pop":
        uris = api.search_genre("pop")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)
    elif genre[0] == "folk":
        uris = api.search_genre("folk")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)
    elif genre[0] == "country":
        uris = api.search_genre("country")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)
    elif genre[0] == "metal":
        uris = api.search_genre("metal")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)
    elif genre[0] == "classical":
        uris = api.search_genre("classical")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)
    elif genre[0] == "jazz":
        uris = api.search_genre("jazz")
        urls = api.get_song_urls(uris)
        names = api.get_song_titles(uris)
        images = api.get_album_cover(uris)
        artists = api.get_artist(uris)

    print(urls)

    print(names)
    jsondata = []
    for url, name, image, artist in zip(urls, names, images, artists):
        if not url.find("No Preview Available At This Time") > -1:
            jsondata.append(
                {"url": url, "name": name, "image": image, "artist": artist}
            )
            print(str(jsondata))
    return flask.jsonify({"songs": jsondata})


app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(
        host=os.getenv("IP", "0.0.0.0"), port=int(os.getenv("PORT", "8080")), debug=True
    )
