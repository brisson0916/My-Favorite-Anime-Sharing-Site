import os
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Float, DateTime, desc
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import EditAnimeForm, AddAnimeForm, CreateAnimeListForm, RegisterForm, LoginForm
from dotenv import load_dotenv
from datetime import datetime
import requests

app = Flask(__name__)
load_dotenv(".env")
app.config['SECRET_KEY'] = os.getenv('FLASK_KEY')
bootstrap = Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anime_database.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

    anime_list = relationship("AnimeList",back_populates="author")

class AnimeList(db.Model):
    __tablename__ = "anime_list"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user.id"))

    author = relationship("User",back_populates="anime_list")
    anime_entry = relationship("AnimeEntry", back_populates="anime_list")

class AnimeEntry(db.Model):
    __tablename__ = "anime_entry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    anime_list_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("anime_list.id"))
    anime_list = relationship("AnimeList", back_populates="anime_entry")

    title: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float(10))
    ranking: Mapped[int] = mapped_column(Integer)
    review: Mapped[str] = mapped_column(String)
    img_url: Mapped[str] = mapped_column(String, nullable=False)
    mal_url: Mapped[str] = mapped_column(String)

with app.app_context():
    db.create_all()

# with app.app_context():
#     new_user = User(
#         email="admin@email.com",
#         name="admin",
#         password="123456"
#     )
#     db.session.add(new_user)
#     db.session.commit()
#
# with app.app_context():
#     new_user = User(
#         email="aaa@aaaa.com",
#         name="user",
#         password="123456"
#     )
#     db.session.add(new_user)
#     db.session.commit()
#
# with app.app_context():
#     new_anime_list = AnimeList(
#         name="Brisson's List",
#         author_id=1
#     )
#     db.session.add(new_anime_list)
#     db.session.commit()
#
# with app.app_context():
#     new_anime_list = AnimeList(
#         name="User's List",
#         author_id=2
#     )
#     db.session.add(new_anime_list)
#     db.session.commit()
#
# with app.app_context():
#     new_anime_entry = AnimeEntry(
#         anime_list_id=2,
#         title="Clannad: After Story",
#         year=2008,
#         description="A high school student who cares little about school or his future decides to help a lonely girl repeating her final year in re-establishing the school's drama club.",
#         rating=8.93,
#         ranking=2,
#         review="It made me cry. Hard.",
#         img_url="https://cdn.myanimelist.net/images/anime/1299/110774l.jpg",
#         mal_url="https://myanimelist.net/anime/4181/Clannad__After_Story"
#     )
#     db.session.add(new_anime_entry)
#     db.session.commit()
#
# with app.app_context():
#     new_anime_entry = AnimeEntry(
#         anime_list_id=2,
#         title="Test",
#         year=2008,
#         description="A high school student who cares little about school or his future decides to help a lonely girl repeating her final year in re-establishing the school's drama club.",
#         rating=10.0,
#         ranking=9,
#         review="It made me cry. Hard.",
#         img_url="https://cdn.myanimelist.net/images/anime/1299/110774l.jpg",
#         mal_url="https://myanimelist.net/anime/4181/Clannad__After_Story"
#     )
#     db.session.add(new_anime_entry)
#     db.session.commit()

@login_manager.user_loader
def load_user(user_id):
   return User.query.get(user_id)

def list_ownership_required(function):
    @wraps(function)
    def decorated_function(anime_list_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))  # Redirect to login page
        anime_list = AnimeList.query.get_or_404(anime_list_id)  # Get the anime list from database
        if not anime_list.author_id == current_user.id and not current_user.id == 1:  # If both not owner and not admin
            abort(403) # Forbidden access
        return function(anime_list_id, *args, **kwargs)
    return decorated_function

def entry_ownership_required(function):
    @wraps(function)
    def decorated_function(anime_entry_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))  # Redirect to login page
        anime_entry = AnimeEntry.query.get_or_404(anime_entry_id)
        user_id = anime_entry.anime_list.author_id  #get author_id from anime list from anime entry
        if not user_id == current_user.id and not current_user.id == 1:  # If both not owner and not admin
            abort(403)  # Forbidden access
        return function(anime_entry_id, *args, **kwargs)
    return decorated_function

@app.route("/", methods=['GET','POST'])
def home():
    result = db.session.execute(db.select(AnimeList).order_by(desc(AnimeList.date_modified)))
    all_lists = result.scalars().all()
    return render_template("index.html", all_lists=all_lists)

@app.route("/register", methods=['GET','POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        check_is_registered = db.session.execute(db.select(User).where(User.email == request.form.get("email"))).scalar()
        if check_is_registered:
            flash('That Email is already registered. Please Login instead!')
            return redirect(url_for('login'))

        #use sha256 encryption on password and add salt
        hash_and_salted_password = generate_password_hash(
            register_form.password.data,
            method="pbkdf2:sha256",
            salt_length=8
        )

        new_user = User(
            email=register_form.email.data,
            name=register_form.name.data,
            password=hash_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template("register.html", register_form=register_form)

@app.route("/login", methods=['GET','POST'])
def login():
    login_form = LoginForm()
    user = db.session.execute(db.select(User).where(User.email == request.form.get("email"))).scalar()

    if request.args.get('message'):
        flash(request.args.get('message'))

    if login_form.validate_on_submit():
        if not user: #if the email is not registered
            flash('That Email does not exist. Please Try Again!')
            return redirect(url_for('login'))
        if check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Incorrect Credentials. Please Try Again!')
            return redirect(url_for('login'))

    return render_template("login.html", login_form=login_form)

@app.route('/logout')
def logout():
    logout_user()
    #some buttons on the website will trigger logout and redirect to login page
    if request.args.get('message'):
        flash(request.args.get('message'))
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))

@app.route("/author/<author_name>", methods=['GET','POST'])
def lists_by_selected_author(author_name):
    author_lists = db.session.execute(
        db.select(AnimeList)
        .join(User)  # Joins the AnimeList table with the User table based on the foreign key relationship defined
        .where(User.name == author_name)  # Filter by user's name
        .order_by(AnimeList.date_modified)
    ).scalars().all()
    view_author = author_name #pass in author_name when user clicks on a list's author to view that author's lists
    return render_template("index.html", all_lists=author_lists, view_author=view_author)

@app.route("/add_anime/<anime_list_id>", methods=['GET','POST'])
@list_ownership_required
def add_anime(anime_list_id):
    add_anime_form = AddAnimeForm()

    if add_anime_form.validate_on_submit():
        query_title = add_anime_form.title.data
        #use jikan API, which fetches data from the MyAnimeList website
        # search for tv anime only and exclude NSFW content
        parameters = {'q': query_title, 'type':"tv",'sfw': 1, 'order_by': 'popularity'}
        response = requests.get(url="https://api.jikan.moe/v4/anime", params=parameters)
        response.raise_for_status()
        # pprint.pp(response.json())
        anime_data = response.json()
        return render_template("select_anime.html", anime_data=anime_data, anime_list_id=anime_list_id)

    return render_template("add_anime.html", form=add_anime_form, anime_list_id=anime_list_id)

@app.route("/select_anime/<anime_list_id>")
@list_ownership_required
def select_anime(anime_list_id):
    new_anime_entry = AnimeEntry(
        anime_list_id=anime_list_id,
        title=request.args.get('title'),
        year=request.args.get('year'),
        description=request.args.get('synopsis'),
        rating=request.args.get('rating'),
        ranking=9999,
        review=request.args.get('review'),
        img_url=request.args.get('img_url'),
        mal_url=request.args.get('mal_url')
    )
    db.session.add(new_anime_entry)
    db.session.commit()
    return redirect(url_for('edit_anime', anime_entry_id=new_anime_entry.id))

@app.route("/edit_anime/<anime_entry_id>", methods=['GET','POST'])
@entry_ownership_required
def edit_anime(anime_entry_id):
    edit_anime_form = EditAnimeForm()
    anime_to_update = db.session.execute(db.select(AnimeEntry).where(AnimeEntry.id == anime_entry_id)).scalar()

    if edit_anime_form.validate_on_submit():
        anime_to_update.rating = edit_anime_form.rating.data
        anime_to_update.review = edit_anime_form.review.data
        anime_to_update.anime_list.date_modified = datetime.now()
        db.session.commit()
        return redirect(url_for('show_list', anime_list_id=anime_to_update.anime_list.id))

    return render_template("edit_anime.html", form=edit_anime_form, anime=anime_to_update)

@app.route("/anime_list/<anime_list_id>")
def show_list(anime_list_id):
    #Show all entries for the list selected, by filtering by anime_list_id
    all_entries = db.session.execute(
        db.select(AnimeEntry)
        .where(AnimeEntry.anime_list_id == anime_list_id)
        .order_by(AnimeEntry.rating)
    ).scalars().all()

    #currently all anime entries is sort by rating
    #loop through entries, assign ranking based on rating
    total_anime_in_list = AnimeEntry.query.filter(AnimeEntry.anime_list_id == anime_list_id).count()
    for anime in all_entries:
        anime.ranking = total_anime_in_list
        db.session.commit()
        total_anime_in_list -= 1

    # refer to the anime_list object to get the name and author of the list (to pass into html template)
    anime_list = db.get_or_404(AnimeList, anime_list_id)
    anime_list_name = anime_list.name
    anime_list_author = anime_list.author

    return render_template("list.html", all_entries=all_entries,
                           anime_list_id=anime_list_id, author=anime_list_author, anime_list_name=anime_list_name)

@app.route("/create_list", methods=['GET','POST'])
@login_required
def create_list():
    create_list_form = CreateAnimeListForm()

    if create_list_form.validate_on_submit():
        new_anime_list = AnimeList(
            name=request.form.get('name'),
            author_id=current_user.id
        )
        db.session.add(new_anime_list)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("create_list.html", create_list_form=create_list_form)

@app.route("/delete_list/<anime_list_id>", methods=['GET','POST'])
@list_ownership_required
def delete_list(anime_list_id):
    #deleting list with all its associated entries (to avoid null for anime_list_id for entries in AnimeEntry)
    list_to_delete = db.session.execute(db.select(AnimeList).where(AnimeList.id == anime_list_id)).scalar()
    entries_to_delete = db.session.execute(db.select(AnimeEntry).where(AnimeEntry.anime_list_id == anime_list_id)).scalars().all()

    if request.method == 'POST':
        for entry in entries_to_delete:
            db.session.delete(entry)
        db.session.delete(list_to_delete)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("delete_list.html", list_to_delete=list_to_delete)

@app.route('/delete_anime/<anime_entry_id>', methods=['GET','POST'])
@entry_ownership_required
def delete_anime(anime_entry_id):
    anime_to_delete = db.session.execute(db.select(AnimeEntry).where(AnimeEntry.id == anime_entry_id)).scalar()

    #fetch id of list before the entry itself is deleted
    list_id = anime_to_delete.anime_list.id

    if request.method == 'POST':
        anime_to_delete.anime_list.date_modified = datetime.now()
        db.session.delete(anime_to_delete)
        db.session.commit()
        return redirect(url_for('show_list', anime_list_id=list_id))

    return render_template("delete_anime.html", anime=anime_to_delete)

if __name__ == "__main__":
    app.run(debug=True, port=5002)