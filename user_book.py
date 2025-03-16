import json
from pydantic import BaseModel
from fastapi import HTTPException
from user_blog import delete_user_blog


USERS_FILE = "users_list.json"


# Load existing user data
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Save user data
def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Initialize database
users_db = load_users()


class BookRequest(BaseModel):
    username: str
    book_name: str



def get_user_book_ids(username: str):
    users_db = load_users()

    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Return only the book IDs as a list
    book_ids = list(users_db[username].keys())

    return book_ids


def delete_book_user(username: str, book: str):
    users_db = load_users()

    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Find the key corresponding to the book name
    book_id = None
    for key, value in users_db[username].items():
        if value == book:
            book_id = key
            break

    if book_id is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Remove book using its ID
    del users_db[username][book_id]

    # If the user has no more books, delete the user
    if not users_db[username]:
        del users_db[username]

    save_users(users_db)
    try: 
        delete_user_blog(username, book_id)
    except Exception as e:
        return {'msg': f'faild to delte blog {book_id} with error {e}'}
        

    return {"message": f"Book '{book}' deleted for user '{username}'"}


def add_book_to_user(username: str, book: str, book_id: str):
    users_db = load_users()

    # Ensure user exists, if not, create a new entry
    if username not in users_db:
        users_db[username] = {}

    # Add the book using the provided book_id
    users_db[username][book_id] = book

    # Save updated data
    save_users(users_db)

    return {"message": f"Book '{book}' added to user '{username}'", "book_id": book_id}


def get_user_books_list(username: str):
    users_db = load_users()
    if username not in users_db:
        return {"error": "User not found"}

    # Convert dictionary values to a list of book names
    return list(users_db[username].values())





