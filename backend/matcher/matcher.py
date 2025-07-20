from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def calculate_fit_score ( resume_text: str, job_descriptions: list ) -> list :
    texts = [resume_text] + [job["description"] for job in job_descriptions]

    vectorizer = TfidfVectorizer( stop_words='english' )
    tfidf_matrix = vectorizer.fit_transform( texts )

    resume_vec = tfidf_matrix[0]
    job_vecs = tfidf_matrix[1 :]

    scores = cosine_similarity( resume_vec, job_vecs ).flatten()

    results = []
    for idx, score in enumerate( scores ) :
        job = job_descriptions[idx]
        results.append( {
            "title" : job["title"],
            "company" : job["company"],
            "location" : job["location"],
            "url" : job["url"],
            "fit_score" : round( score * 100, 2 )
        } )

    results.sort( key=lambda x : x["fit_score"], reverse=True )
    return results
