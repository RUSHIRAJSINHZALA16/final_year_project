from typing import List

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from themoviedb import TMDb, Genre, PartialMovie

from ..models import Movie, Rating, db

# If you have the recommendation logic ready, import it here:
# from ..recommendation import get_ai_recommendations

main = Blueprint('main', __name__)

tmdb = TMDb()

@main.route('/')
@login_required
def index():
    # 1. Fetch Movies by Genre for the Netflix Rows
    # Make sure these genres match what you loaded in scripts/load_tmdb.py
    # genres = ["Action", "Comedy", "Drama", "Sci-Fi"]

    # We create a dictionary where each key is a genre and the value is a list of movies
    # genre_data = {
    #     g: Movie.query.filter(Movie.genre.ilike(f'%{g}%')).limit(10).all()
    #     for g in genres
    # }
    genre_data:dict[str,  list[PartialMovie] | None] = {}

    genre_data['Action'] = tmdb.discover().movie(page=1, with_genres='28').results
    genre_data['Comedy'] = tmdb.discover().movie(page=1, with_genres='35').results
    genre_data['Drama'] = tmdb.discover().movie(page=1, with_genres='18').results
    genre_data['Sci-Fi'] = tmdb.discover().movie(page=1, with_genres='878').results

    # 2. Pick a "Featured" movie for the Hero/Top Banner
    # featured = Movie.query.order_by(Movie.tmdb_rating.desc()).first()
    data_featured = tmdb.movies().top_rated().results
    if len(data_featured) > 0:
        featured = data_featured[0]
    else:
        featured = None
    # 3. Render the Netflix-style template
    return render_template('index.html', genre_data=genre_data, featured=featured)


@main.route('/rate/<int:movie_id>', methods=['POST'])
@login_required
def rate(movie_id):
    score = request.form.get('score')
    if not score:
        return redirect(url_for('main.index'))

    # Logic for "Live Rating" - Update if exists, else create
    rating = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if rating:
        rating.score = int(score)
    else:
        new_rating = Rating(user_id=current_user.id, movie_id=movie_id, score=int(score))
        db.session.add(new_rating)

    db.session.commit()
    return redirect(url_for('main.index'))


@main.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.index'))

    # Search for movies where the title contains the query (case-insensitive)
    movies_record = tmdb.search().movies(query=query).results
    # Movie.query.filter(Movie.title.ilike(f'%{query}%')).all()
    print(len(movies_record))
    movies: List[Movie] = []
    genres: List[Genre] = tmdb.genres().movie().results

    if movies_record is not None:
        for m in movies_record:
            genre_name = "Trending"
            if len(m.genre_ids) > 0:
                movie_genra_id = m.genre_ids[0]
                for i, g in enumerate(genres):
                    if g.id == movie_genra_id:
                        genre_name = g.name
                        break

            movies.append(Movie(id=m.id, title=m.title, overview=m.overview, genre=genre_name, poster_path=m.poster_path, tmdb_rating=m.vote_average))
    
    return render_template('search.html', movies=movies, query=query)


@main.route('/movie/<int:movie_id>')
@login_required
def movie_detail_page(movie_id:int):
    if movie_id <= 0:
        return redirect(url_for('main.index'))

    tmdb_movie = tmdb.movie(movie_id)
    movie_detail = tmdb_movie.details()

    if movie_detail is None:
        return redirect(url_for('main.index'))

    movie_recommendations = tmdb_movie.recommendations().results
    movie_similar = tmdb_movie.similar().results
    movie_videos = tmdb_movie.videos().results
    movie_credits = tmdb_movie.credits()
    movie_images = tmdb_movie.images()

    return render_template('movie_detail.html',
                           movie_detail=movie_detail,
                           movie_videos=movie_videos,
                           movie_recommendations=movie_recommendations,
                           movie_similar=movie_similar,
                           movie_credits=movie_credits,
                           movie_images=movie_images
                           )


@main.route('/tv-show/<int:tv_show_id>')
@login_required
def tv_show_detail_page(tv_show_id:int):
    if tv_show_id <= 0:
        return redirect(url_for('main.index'))

    tmdb_tv_show = tmdb.tv(tv_show_id)
    tv_show_detail = tmdb_tv_show.details()

    if tv_show_detail is None:
        return redirect(url_for('main.index'))

    tv_show_recommendations = tmdb_tv_show.recommendations().results
    tv_show_similar = tmdb_tv_show.similar().results
    tv_show_videos = tmdb_tv_show.videos().results
    tv_show_credits = tmdb_tv_show.credits()
    tv_show_images = tmdb_tv_show.images()

    return render_template('tv_show_detail.html',
                           tv_show_detail=tv_show_detail,
                           tv_show_videos=tv_show_videos,
                           tv_show_recommendations=tv_show_recommendations,
                           tv_show_similar=tv_show_similar,
                           tv_show_credits=tv_show_credits,
                           tv_show_images=tv_show_images
                           )
