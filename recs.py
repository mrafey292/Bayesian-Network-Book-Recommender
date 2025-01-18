import pandas as pd
import numpy as np
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from datetime import datetime
from collections import Counter
import ast

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# from fetch import fetch_lists_from_firestore, fetch_genres_from_firestore
# from post import post_recommendations_to_firestore

import json

# Load dataset for comparison
books = pd.read_csv('books_enriched.csv')

# MATCHES
class BookRecommender():
    def __init__(self):
        self.model = BayesianNetwork([
            ('AvgRating', 'Rating'),
            ('GenreMatch', 'Rating'),
            ('ContentMatch', 'Rating'),
            ('Rating', 'Recommendation')
        ])

        # Define states for each variable
        self.genres = [
                        "Art", "Biography", "Business", "Chick Lit", "Children's", "Christian", "Classics",
                        "Comics", "Contemporary", "Cookbooks", "Crime", "Ebooks", "Fantasy", "Fiction",
                        "Graphic Novels", "Historical Fiction", "History", "Horror",
                        "Humor and Comedy", "Manga", "Memoir", "Music", "Mystery", "Nonfiction", "Paranormal",
                        "Philosophy", "Poetry", "Psychology", "Religion", "Romance", "Science", "Science Fiction", 
                        "Self Help", "Suspense", "Spirituality", "Sports", "Thriller", "Travel", "Young Adult"
                    ]
        self.match_levels = ['high', 'medium', 'low']
        self.ratings = ['low', 'medium', 'high']
        self.tfidf_vectorizer = TfidfVectorizer()

        self._initialize_cpds()
        self.inference = VariableElimination(self.model)
    
    def calculate_genre_match(self, book_genres, user_preferred_genres):
        """Calculate how well a book's genres match user preferences"""
        if not book_genres:
            return 'low'
            
        book_genres_list = ast.literal_eval(book_genres)
        
        # Check for direct match with preferred genres
        for book_genre in book_genres_list:
            book_genre = book_genre.strip().lower()
            if book_genre in [genre.lower() for genre in user_preferred_genres]:
                return 'high'
        
        # Check for related genres
        for book_genre in book_genres_list:
            book_genre = book_genre.strip().lower()
            for user_genre in user_preferred_genres:
                if self._are_genres_related(book_genre, user_genre.lower()):
                    return 'medium'
        
        return 'low'
    
    def _are_genres_related(self, genre1, genre2):
        """Define genre relationships (e.g., fantasy and scifi might be related)"""
        related_genres = {
            "art": ["history", "classics"],
            "biography": ["memoir", "history", "nonfiction"],
            "business": ["self help", "psychology", "nonfiction"],
            "chick lit": ["romance", "contemporary", "humor and comedy"],
            "children's": ["young adult", "fantasy", "comics"],
            "christian": ["religion", "spirituality", "self help"],
            "classics": ["fiction", "historical fiction", "philosophy"],
            "comics": ["graphic novels", "manga", "fantasy"],
            "contemporary": ["fiction", "romance", "chick lit"],
            "cookbooks": ["nonfiction", "self help", "travel"],
            "crime": ["mystery", "thriller", "suspense"],
            "ebooks": ["fiction", "nonfiction", "self help"],
            "fantasy": ["science fiction", "young adult", "fiction"],
            "fiction": ["historical fiction", "contemporary", "philosophy"],
            "graphic novels": ["comics", "manga", "fiction"],
            "historical fiction": ["history", "classics", "fiction"],
            "history": ["biography", "nonfiction", "philosophy"],
            "horror": ["thriller", "paranormal", "suspense"],
            "humor and comedy": ["chick lit", "fiction", "memoir"],
            "manga": ["comics", "graphic novels", "young adult"],
            "memoir": ["biography", "self help", "humor and comedy"],
            "music": ["biography", "history", "art"],
            "mystery": ["crime", "thriller", "fiction"],
            "nonfiction": ["biography", "history", "science"],
            "paranormal": ["horror", "fantasy", "thriller"],
            "philosophy": ["psychology", "classics", "religion"],
            "poetry": ["classics", "fiction", "memoir"],
            "psychology": ["self help", "philosophy", "science"],
            "religion": ["christian", "philosophy", "spirituality"],
            "romance": ["chick lit", "contemporary", "young adult"],
            "science": ["science fiction", "nonfiction", "psychology"],
            "science fiction": ["fantasy", "fiction", "thriller"],
            "self help": ["psychology", "nonfiction", "spirituality"],
            "suspense": ["thriller", "crime", "mystery"],
            "spirituality": ["religion", "self help", "philosophy"],
            "sports": ["biography", "nonfiction", "travel"],
            "thriller": ["crime", "mystery", "horror"],
            "travel": ["nonfiction", "cookbooks", "memoir"],
            "young adult": ["fantasy", "romance", "children's"]
        }

        return genre2 in related_genres.get(genre1, [])

    def calculate_content_match(self, book_description, favorite_books_descriptions):
        if not book_description or not favorite_books_descriptions:
            return 0.0
        
        descriptions = [book_description] + favorite_books_descriptions
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(descriptions)
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        return max(cosine_similarities[0])
    

    def _initialize_cpds(self):
        genre_match_cpd = TabularCPD(
            variable='GenreMatch',
            variable_card=3,
            values=[[0.45], [0.35], [0.20]]  # [low, medium, high] - Most books won't be exact genre matches
        )

        content_match_cpd = TabularCPD(
            variable='ContentMatch',
            variable_card=3,
            values=[[0.50], [0.35], [0.15]]  # Content matches are typically lower
        )

        avg_rating_cpd = TabularCPD(
            variable='AvgRating',
            variable_card=3,
            values=[[0.20], [0.50], [0.30]]  # Most books cluster around medium ratings
        )

        rating_cpd = TabularCPD(
            variable='Rating',
            variable_card=3,
            values=[
                [0.95, 0.90, 0.85, 0.70, 0.65, 0.60, 0.45, 0.40, 0.35,  # Low rating probabilities
                0.65, 0.60, 0.55, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15,
                0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.15, 0.10, 0.05],
                [0.04, 0.08, 0.12, 0.25, 0.28, 0.30, 0.40, 0.42, 0.45,  # Medium rating probabilities
                0.30, 0.32, 0.35, 0.45, 0.47, 0.50, 0.45, 0.47, 0.50,
                0.45, 0.47, 0.50, 0.45, 0.47, 0.50, 0.35, 0.37, 0.40],
                [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.18, 0.20,  # High rating probabilities
                0.05, 0.08, 0.10, 0.15, 0.18, 0.20, 0.30, 0.33, 0.35,
                0.15, 0.18, 0.20, 0.30, 0.33, 0.35, 0.50, 0.53, 0.55],
            ],
            evidence=['GenreMatch', 'ContentMatch', 'AvgRating'],
            evidence_card=[3, 3, 3]
        )

        recommendation_cpd = TabularCPD(
            variable='Recommendation',
            variable_card=2,
            values=[
                [0.98, 0.60, 0.20],  # Not recommend probabilities
                [0.02, 0.40, 0.80]   # Recommend probabilities - More conservative
            ],
            evidence=['Rating'],
            evidence_card=[3]
        )

        self.model.add_cpds(genre_match_cpd, content_match_cpd, avg_rating_cpd, rating_cpd, recommendation_cpd)
        
    def get_recommendation(self, genre_match, content_match, avg_rating):
        evidence = {
            'GenreMatch': self.match_levels.index(genre_match),
            'ContentMatch': 0 if content_match < 0.3 else (1 if content_match < 0.5 else 2),  # Adjusted thresholds
            'AvgRating': 0 if avg_rating < 3.5 else (1 if avg_rating < 4.2 else 2)  # Adjusted rating thresholds
        }
        
        result = self.inference.query(['Recommendation'], evidence=evidence)
        recommend_prob = result.values[1]
        
        return recommend_prob


def generate_recommendations(lists_data, preferred_genres):
    recommender = BookRecommender()

    # Calculate genre match, content match, and recommendation probability for all books
    recommendations = []
    read_books = lists_data.get('Read', {}).get('books', [])
    
    # Sort books by rating (descending) and timestamp (most recent first)
    sorted_books = sorted(read_books, key=lambda x: (-x['rating'], x.get('timestamp', '')), reverse=False)
    
    # Return the top n books
    favorite_books = sorted_books[:10]
    favorite_books_descriptions = [book['author'] + " " + book['description'] for book in favorite_books]

    for index, book in books.iterrows():
        book_genres = book['genres'] if pd.notna(book['genres']) else ""
        avg_rating = float(book['average_rating']) if pd.notna(book['average_rating']) else 0.0
        book_desc = book['description'] if pd.notna(book['description']) else ""  # Replace NaN with empty string

        genre_match = recommender.calculate_genre_match(book_genres, preferred_genres)
        content_match = recommender.calculate_content_match(book['authors'] + " " + book_desc, favorite_books_descriptions)

        if (content_match < 0.3) and (genre_match == 'low'):
            continue
        
        recommend_prob = recommender.get_recommendation(genre_match, content_match, avg_rating)

        recommendations.append({
            'title': book['title'],
            'author': book['authors'],
            'genre': book_genres,
            'description': book_desc,
            'avg_rating': avg_rating,
            'genre_match': genre_match,
            'content_match': content_match,
            'recommend_prob': recommend_prob,
            'isbn10': book['isbn'],
            'isbn13': book['isbn13'],
            'coverImageUrl': book['image_url']
        })

    # Sort recommendations by recommendation probability (descending) and take the top 10
    top_recommendations = sorted(recommendations, key=lambda x: x['recommend_prob'], reverse=True)[:10]

    print("Recommendations generated")
    return top_recommendations


# lists_data = fetch_lists_from_firestore('gS1lmKV5ILROSQvPGdDlzAozvOf1')
# preferred_genres = fetch_genres_from_firestore('gS1lmKV5ILROSQvPGdDlzAozvOf1')

# recommendations = generate_recommendations(lists_data, preferred_genres)
# # Print the top 10 recommendations based on recommendation probability
# print("\nTop 10 Book Recommendations based on recommendation probability:")
# for i, rec in enumerate(recommendations, 1):
#     print(f"\n{i}. Title: {rec['title']}")
#     print(f"   Author: {rec['author']}")
#     print(f"   Genre: {rec['genre']}")
#     print(f"   Description: {rec['description']}")
#     print(f"   Average Rating: {rec['avg_rating']}")
#     print(f"   Genre Match: {rec['genre_match']}")
#     print(f"   Content Match: {rec['content_match']:.2f}")
#     print(f"   Recommendation Probability: {rec['recommend_prob']:.2f}")




# post_recommendations_to_firestore('gS1lmKV5ILROSQvPGdDlzAozvOf1', recommendations)
