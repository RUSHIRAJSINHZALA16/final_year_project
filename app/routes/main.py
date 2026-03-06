import random
from typing import List

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from themoviedb import TMDb, Genre, PartialMovie, PartialTV

from ..models import Movie, Rating, WatchlistItem, db

# If you have the recommendation logic ready, import it here:
# from recommendation import get_ai_recommendations

main = Blueprint('main', __name__)

tmdb = TMDb()

@main.route('/')
@login_required
def index():
    query = request.args.get('type', '').strip().lower()

    is_movie = False
    is_tv_show = False

    if not query:
        is_movie = True
        is_tv_show = True
    elif query == 'movie':
        is_movie = True
    elif query == 'tv-show':
        is_tv_show = True

    movie_featured: PartialMovie | None = None
    tv_show_featured: PartialTV | None = None

    movie_genre_data: dict[str, list[PartialMovie] | None] | None = None
    tv_show_genre_data: dict[str, list[PartialTV] | None] | None = None

    if is_movie:
        movie_genre_data = {
            'Action': tmdb.discover().movie(page=1, with_genres='28').results,
            'Comedy': tmdb.discover().movie(page=1, with_genres='35').results,
            'Drama': tmdb.discover().movie(page=1, with_genres='18').results,
            'Sci-Fi': tmdb.discover().movie(page=1, with_genres='878').results
        }

        # 2. Pick a "Featured" movie for the Hero/Top Banner
        # featured = Movie.query.order_by(Movie.tmdb_rating.desc()).first()
        data_featured = tmdb.movies().top_rated().results
        if len(data_featured) > 0:
            movie_featured = data_featured[0]

    if is_tv_show:
        tv_show_genre_data: dict[str, list[PartialMovie] | None] = {
            'Action & Adventure': tmdb.discover().tv(page=1, with_genres='10759').results,
            'Comedy': tmdb.discover().tv(page=1, with_genres='35').results,
            'Drama': tmdb.discover().tv(page=1, with_genres='18').results,
            'Sci-Fi & Fantasy': tmdb.discover().tv(page=1, with_genres='10765').results
        }

        # 2. Pick a "Featured" movie for the Hero/Top Banner
        # featured = Movie.query.order_by(Movie.tmdb_rating.desc()).first()
        data_featured1 = tmdb.tvs().top_rated().results
        if len(data_featured1) > 0:
            tv_show_featured = data_featured1[0]

    show_featured_movie = True
    if is_tv_show and is_movie:
        show_featured_movie = random.uniform(0, 1) > 0.5
    elif is_tv_show:
        show_featured_movie = False
    elif is_movie:
        show_featured_movie = True

    # 3. Render the Netflix-style template
    return render_template('index.html',
                           show_featured_movie=show_featured_movie,
                           is_movie=is_movie,
                           is_tv_show=is_tv_show,
                           movie_genre_data=movie_genre_data,
                           movie_featured=movie_featured,
                           tv_show_genre_data=tv_show_genre_data,
                           tv_show_featured=tv_show_featured
                           )


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

@main.route('/toggle-watchlist/<media_type>/<int:item_id>', methods=['POST'])
@login_required
def toggle_watchlist(media_type, item_id):
    if media_type not in ['movie', 'tv']:
        return redirect(request.referrer or url_for('main.index'))
        
    title = request.form.get('title')
    poster_path = request.form.get('poster_path')
    
    # Check if item is already in watchlist
    existing_item = WatchlistItem.query.filter_by(
        user_id=current_user.id, 
        item_id=item_id, 
        media_type=media_type
    ).first()
    
    if existing_item:
        db.session.delete(existing_item)
    else:
        new_item = WatchlistItem(
            user_id=current_user.id,
            item_id=item_id,
            media_type=media_type,
            title=title,
            poster_path=poster_path
        )
        db.session.add(new_item)
        
    db.session.commit()
    return redirect(request.referrer or url_for('main.index'))

@main.route('/my-list')
@login_required
def my_list():
    items = WatchlistItem.query.filter_by(user_id=current_user.id).order_by(WatchlistItem.timestamp.desc()).all()
    return render_template('my_list.html', items=items)

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
    movie_detail = tmdb_movie.details(append_to_response="recommendations,similar,videos,credits,images")

    if movie_detail is None:
        return redirect(url_for('main.index'))
    
    # Check if in watchlist
    in_watchlist = WatchlistItem.query.filter_by(
        user_id=current_user.id, 
        item_id=movie_id, 
        media_type='movie'
    ).first() is not None

    return render_template('movie_detail.html',
                           movie_detail=movie_detail,
                           in_watchlist=in_watchlist
                           )


@main.route('/tv-show/<int:tv_show_id>')
@login_required
def tv_show_detail_page(tv_show_id:int):
    if tv_show_id <= 0:
        return redirect(url_for('main.index'))

    tmdb_tv_show = tmdb.tv(tv_show_id)
    tv_show_detail = tmdb_tv_show.details(append_to_response="recommendations,similar,videos,credits,images")

    if tv_show_detail is None:
        return redirect(url_for('main.index'))
    
    # Check if in watchlist
    in_watchlist = WatchlistItem.query.filter_by(
        user_id=current_user.id, 
        item_id=tv_show_id, 
        media_type='tv'
    ).first() is not None

    return render_template('tv_show_detail.html',
                           tv_show_detail=tv_show_detail,
                           in_watchlist=in_watchlist
                           )
