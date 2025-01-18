import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firestore DB

def fetch_lists_from_firestore(userID, db):
    user_doc_ref = db.collection('lists').document(userID)
    lists = {
        "Read": {"books": []},
        "Currently Reading": {"books": []},
        "Want to Read": {"books": []}
    }

    subcollections = {
        "already_read": "Read",
        "currently_reading": "Currently Reading",
        "want_to_read": "Want to Read"
    }

    for subcollection, list_name in subcollections.items():
        books_ref = user_doc_ref.collection(subcollection)
        books = books_ref.stream()
        for book in books:
            book_data = book.to_dict()
            if book_data is None:
                print(f"Warning: No data found for book in subcollection {subcollection}")
                continue

            book_id = book_data.get("bookId")
            if book_id is None:
                print(f"Warning: No bookId found for book in subcollection {subcollection}")
                continue

            book_info_ref = db.collection('books').document(book_id)
            book_info_data = book_info_ref.get().to_dict()
            if book_info_data is None:
                # print(f"Warning: No book info found for bookId {book_id}")
                continue

            author = book_info_data.get("author")
            if author is None:
                print(f"Warning: No author found for bookId {book_id}")
                author_list = ["Unknown"]
            else:
                author_list = [author.strip().strip('"') for author in author.split(',')]

            book_info = {
                "title": book_info_data.get("title"),
                "author": ', '.join(author_list),
                "genre": book_info_data.get("genre") if isinstance(book_info_data.get("genre"), list) else [book_info_data.get("genre")],
                "description": book_info_data.get("description").replace('"', '')
            }
            if subcollection == "already_read":
                book_info["rating"] = book_data.get("rating")
                timestamp = book_data.get("timestamp")
                if timestamp:
                    book_info["timestamp"] = timestamp.isoformat()
            lists[list_name]["books"].append(book_info)

    print("Lists fetched for user", userID)
    return lists

def fetch_genres_from_firestore(userID, db):
    user_doc_ref = db.collection('user').document(userID)
    user_data = user_doc_ref.get().to_dict()
    preferred_genres = user_data.get('preferredGenres', [])
    print("Genres fetched for user", userID)

    return preferred_genres

def export_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

# # Fetch the data
# data = fetch_lists_from_firestore('gS1lmKV5ILROSQvPGdDlzAozvOf1')

# # Export the data to a JSON file
# export_to_json(data, 'user_books.json')

# preferred_genres = fetch_genres_from_firestore('gS1lmKV5ILROSQvPGdDlzAozvOf1')
# print(preferred_genres[0])