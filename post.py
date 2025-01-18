import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import ast

def post_recommendations(userID, recommendations, db):
    book_ids = []

    for book in recommendations:
        try:
            if isinstance(book.get('author'), list):
                book['author'] = book['author'][0]

            if isinstance(book.get('genre'), str):
                try:
                    book['genre'] = ast.literal_eval(book['genre'])
                except (ValueError, SyntaxError):
                    book['genre'] = []

            if not isinstance(book.get('isbn10'), str):
                book['isbn10'] = str(book['isbn10'])
            if not isinstance(book.get('isbn13'), str):
                book['isbn13'] = str(book['isbn13'])

            book_data = {
                'author': book.get('author', 'Unknown'),
                'coverImageUrl': book.get('coverImageUrl', ''),
                'description': book.get('description', 'No description available'),
                'genre': book.get('genre', []),
                'isbn10': book.get('isbn10'),
                'isbn13': book.get('isbn13'),
                'title': book.get('title', 'No title provided')
            }

            # Create new document with auto-generated ID
            doc_ref = db.collection('books').document()
            doc_ref.set(book_data)
            book_ids.append(doc_ref.id)

        except Exception as e:
            print(f"Error posting book {book.get('title', 'Unnamed')}: {e}")
            continue

    recommendation_data = {
        'bookIDs': book_ids,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'userID': userID
    }

    try:
        recommendation_ref = db.collection('recommendations').document(userID)
        recommendation_ref.set(recommendation_data, merge=True)
        print(f'Recommendations posted for user {userID}')
    except Exception as e:
        print(f"Error posting recommendations: {e}")

        
# Example usage
# if __name__ == "__main__":
#     userID = 'gS1lmKV5ILROSQvPGdDlzAozvOf1'
#     recommendations = [
#         {
#             'author': 'Author Name',
#             'coverImageUrl': 'http://example.com/image.jpg',
#             'description': 'Book description',
#             'genre': 'Fiction',
#             'isbn10': '1234567890',
#             'isbn13': '123-1234567890',
#             'title': 'Book Title'
#         },
#         # Add more book recommendations as needed
#     ]
#     post_recommendations(userID, recommendations)
