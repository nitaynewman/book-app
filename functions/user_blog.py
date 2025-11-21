from pydantic import BaseModel
from helper.supabase import supabase_service

class BlogRequest(BaseModel):
    username: str
    book_id: str
    title: str
    description: str
    subject_places: str
    subject_times: str
    subjects: str
    thoughts: str

def add_blog_user(username: str, title: str, description: str, subject_places: str, 
                 subject_times: str, subjects: str, book_id: str, thoughts: str):
    """Add or update a blog entry for a user's book"""
    try:
        supabase_service.add_user_blog(
            username=username,
            book_id=book_id,
            title=title,
            description=description,
            subject_places=subject_places,
            subject_times=subject_times,
            subjects=subjects,
            thoughts=thoughts
        )
        
        return {'msg': f'Blog "{title}" added successfully!'}
    
    except Exception as e:
        return {'msg': f'Failed with this error: {e}'}

def get_user_blog(username: str, book_id: str):
    """Get a specific blog entry for a user's book"""
    try: 
        blog = supabase_service.get_user_blog(username, book_id)
        
        if not blog:
            return 'no user or blogs for the user'
        
        return blog
        
    except Exception as e:
        return f'failed to return book id {book_id} with error: {e}'

def delete_user_blog(username: str, book_id: str):
    """Delete a blog entry for a user's book"""
    try:
        result = supabase_service.delete_user_blog(username, book_id)
        
        if not result:
            return 'no user or blogs for the user'
        
        return {'msg': f'book {book_id} deleted successfully'}
    
    except Exception as e:
        return {'msg': f'Failed to delete blog: {str(e)}'}