import json
from pydantic import BaseModel

USER_BLOG_FILE = 'users_blog.json'

def load_blogs():
    try: 
        with open(USER_BLOG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f'failed to create with error: {e}')
        return {}

def save_blog(data):
    with open(USER_BLOG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

blog_db = load_blogs()

class BlogRequest(BaseModel):
    username: str
    book_id: str
    title: str
    description: str
    subject_places: str
    subject_times: str
    subjects: str
    thoughts: str

def add_blog_user(username: str, title: str, description: str, subject_places: str, subject_times: str, subjects: str, book_id: str, thoughts: str):
    try:
        blog_db = load_blogs()  # Load the database

        if username not in blog_db:
            blog_db[username] = {}

        # Ensure the book entry exists
        blog_db[username][book_id] = {
            "book_id": book_id,
            "title": title,
            "description": description,
            "subject_places": subject_places,
            "subject_times": subject_times,
            "subjects": subjects,
            "thoughts": thoughts,
        }

        save_blog(blog_db)  # Save the updated database
        
        return {'msg': f'Blog "{title}" added successfully!'}
    
    except Exception as e:
        return {'msg': f'Failed with this error: {e}'}


def get_user_blog(username: str, book_id: str):
    try: 
        blog_db = load_blogs()
        if username not in blog_db or book_id not in blog_db[username]:
            return 'no user or blogs for the user'
        return blog_db[username][book_id]
        
    except Exception as e:
        return f'failed to return book id {book_id} with error: {e}'
        
def delete_user_blog(username: str, book_id: str):
    blog_db = load_blogs()
    if username not in blog_db:
        return 'no user or blogs for the user'
    if book_id not in blog_db[username]:
        return 'no such book id for user'
    
    del blog_db[username][book_id]

    save_blog(blog_db)
    return {'msg': f'book {book_id} deleted successfuly'}