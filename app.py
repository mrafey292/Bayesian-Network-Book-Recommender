from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from fetch import fetch_lists_from_firestore, fetch_genres_from_firestore
from recs import generate_recommendations
from post import post_recommendations

# Initialize Firebase Admin SDK
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
CORS(app)

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Endpoint to generate recommendations for a user.
    Expects a POST request with JSON containing the `userID`.
    """
    print("Request received from:", request.remote_addr)  # Logs the IP of the incoming request
    try:
        # Parse and validate request data
        data = request.get_json()
        userID = data.get("userID")

        print("User ID:", userID)
        if not userID:
            return jsonify({"error": "UserID not provided"}), 400

        # Step 1: Fetch user data from Firestore
        try:
            lists_data = fetch_lists_from_firestore(userID, db)
            preferred_genres = fetch_genres_from_firestore(userID, db)
        except Exception as e:
            print("Error fetching data from Firestore:", str(e))
            return jsonify({"error": f"Failed to fetch data from Firestore: {str(e)}"}), 500

        # Step 2: Generate recommendations
        try:
            recommendations = generate_recommendations(lists_data, preferred_genres)
        except Exception as e:
            print("Error generating recommendations:", str(e))
            return jsonify({"error": f"Failed to generate recommendations: {str(e)}"}), 500

        # Step 3: Store recommendations in Firestore
        try:
            post_recommendations(userID, recommendations, db)
        except Exception as e:
            print("Error posting recommendations to Firestore:", str(e))
            return jsonify({"error": f"Failed to post recommendations to Firestore: {str(e)}"}), 500

        # Step 4: Return recommendations to the client
        return jsonify({"status": "success", "recommendations": recommendations}), 200

    except Exception as e:
        # Handle unexpected server errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    # Run the server and allow connections from other devices
    app.run(host="0.0.0.0", port=5000, debug=True)
