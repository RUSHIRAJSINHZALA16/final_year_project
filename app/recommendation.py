import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Movie


def get_ai_recommendations(movie_title):
    movies = Movie.query.all()
    if not movies: return []

    df = pd.DataFrame([{'title': m.title, 'content': f"{m.title} {m.overview}"} for m in movies])

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['content'].fillna(''))
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    try:
        idx = df.index[df['title'] == movie_title][0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:7]
        movie_indices = [i[0] for i in sim_scores]
        return df.iloc[movie_indices]['title'].tolist()
    except:
        return []