from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, ValidationError
import requests
import re
import os

tmdb_api = os.environ["tmdb_api"]
tmdb_url = "https://api.themoviedb.org/3/search/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["FLASK_SECRET_KEY"]
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_collection_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def review_check(form, field):
    reg = "^[0-9]\d*(\.\d+)?$"
    result = re.search(reg, field.data)
    if not result:
        raise ValidationError('Pleases enter valid Rating')


class EditForm(FlaskForm):
    rating = StringField(label='Your Rating Out of 10 e.g 7.5', validators=[InputRequired(), review_check])
    review = StringField(label='Your Review', validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.VARCHAR(250), unique=True, nullable=False)
    year = db.Column(db.VARCHAR(250), nullable=False)
    description = db.Column(db.VARCHAR(500), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.VARCHAR(500))
    img_url = db.Column(db.VARCHAR(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


db.create_all()


@app.route("/")
def home():
    # all_movies = db.session.query(Movie).order_by(desc(Movie.rating)).all()
    #
    # for i in range(len(all_movies)):
    #     # This line gives each movie a new ranking
    #     all_movies[i].ranking = i + 1

    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get('id')

    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(tmdb_url, params={"api_key": tmdb_api, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", movies=data)

    return render_template("add.html", form=form)


@app.route('/get_movie')
def get_movie():
    movie_id = request.args.get('id')
    tmdb_movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url=tmdb_movie_url, params={"api_key": tmdb_api}).json()
    img_url = f"https://www.themoviedb.org/t/p/original/{response['poster_path']}"
    new_movie = Movie(id=movie_id, title=response["original_title"], year=response["release_date"],
                      description=response["overview"], img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
