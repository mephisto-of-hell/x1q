# database.py
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
import datetime

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def init_db():
    """Initialize the database by creating unique indexes."""
    db.questions.create_index("id", unique=True)
    db.user_scores.create_index([("group_id", 1), ("user_id", 1)], unique=True)

def get_group_settings(group_id):
    """Get settings for a group by its ID."""
    return db.group_settings.find_one({"_id": group_id})

def set_group_language(group_id, language):
    """Set or update the language for a group."""
    db.group_settings.update_one(
        {"_id": group_id},
        {"$set": {"language": language}},
        upsert=True
    )

def get_random_question(language):
    """Get a random question for the specified language."""
    pipeline = [
        {"$match": {"language": language}},
        {"$sample": {"size": 1}}
    ]
    result = list(db.questions.aggregate(pipeline))
    return result[0] if result else None

def insert_active_poll(poll_id, group_id, question_id):
    """Insert a new active poll record."""
    db.active_polls.insert_one({
        "_id": poll_id,
        "group_id": group_id,
        "question_id": question_id,
        "timestamp": datetime.datetime.utcnow()
    })

def get_question_by_poll_id(poll_id):
    """Get question and group ID by poll ID."""
    active_poll = db.active_polls.find_one({"_id": poll_id})
    if active_poll:
        question = db.questions.find_one({"id": active_poll["question_id"]})
        if question:
            return {"question": question, "group_id": active_poll["group_id"]}
    return None

def update_user_score(group_id, user_id, increment):
    """Update or initialize a user's score in a group."""
    db.user_scores.update_one(
        {"group_id": group_id, "user_id": user_id},
        {"$inc": {"score": increment}},
        upsert=True
    )