from typing import List

import requests, os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import Movie
from themoviedb import TMDb, Genre


def seed():
    app = create_app()
    with app.app_context():
        # Map TMDB IDs to Genre Names
        #GENRES = {28: "Action", 35: "Comedy", 18: "Drama", 878: "Sci-Fi"}
        api_key = os.getenv('TMDB_API_KEY')

        tmdb = TMDb()

        popular_movies = tmdb.movies().popular().results

        for m in popular_movies:
            if not Movie.query.get(m.id):
                GENRES: List[Genre] = tmdb.genres().movie().results;

                movie_generes: List[str] = [str(x.name) for x in GENRES if m.genre_ids.count(x.id) > 0]

                if len(movie_generes) == 0:
                    movie_generes.append('Tranding')

                movie = Movie(id=m.id, title=m.title, overview=m.overview,
                              genre=movie_generes[0], poster_path=m.poster_path, tmdb_rating=m.vote_average)
                db.session.add(movie)
        db.session.commit()
        print("Local Postgres 18 Populated with {} movies!".format(len(popular_movies)))


if __name__ == "__main__":
    seed()