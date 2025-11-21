from pydantic import BaseModel
from fastapi import HTTPException
from helper.supabase import supabase_service

class BookRequest(BaseModel):
    username: str
    book_name: str

def get_user_book_ids(username: str):
    """Get all book IDs for a user"""
    try:
        book_ids = supabase_service.get_user_book_ids(username)
        if not book_ids:
            raise HTTPException(status_code=404, detail="User not found or no books")
        return book_ids
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def delete_book_user(username: str, book: str):
    """Delete a book from user's collection and associated blog"""
    try:
        # Delete the book and get its book_id
        book_id = supabase_service.delete_user_book(username, book)
        
        # Try to delete associated blog
        try:
            supabase_service.delete_user_blog(username, book_id)
        except Exception as e:
            print(f'Failed to delete blog {book_id} with error {e}')
        
        return {"message": f"Book '{book}' deleted for user '{username}'"}
    
    except Exception as e:
        if "Book not found" in str(e):
            raise HTTPException(status_code=404, detail="Book not found")
        raise HTTPException(status_code=500, detail=str(e))

def add_book_to_user(username: str, book: str, book_id: str):
    """Add a book to user's collection"""
    try:
        supabase_service.add_user_book(username, book, book_id)
        return {"message": f"Book '{book}' added to user '{username}'", "book_id": book_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_user_books_list(username: str):
    """Get list of all books for a user"""
    try:
        books = supabase_service.get_user_books(username)
        if not books:
            return {"error": "User not found or no books"}
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))