import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(url, key)
    
    #----------- book_app_users functions -----------------#
    def add_user(self, username: str, email: str):
        """Add a new user to the system"""
        if self.check_user(username):
          raise Exception(f"Username '{username}' already exists")
        
        existing_email = self.get_user_by_email(email)
        if existing_email:
          raise Exception(f"Email '{email}' already registered")
        try:
            data = {
                "username": username,
                "email": email,
            }
            response = self.client.table("book_app_users").insert(data).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to add user: {str(e)}")
    
    def check_user(self, username: str):
        """Check if user exists"""
        try:
            response = self.client.table("book_app_users")\
                .select("username")\
                .eq("username", username)\
                .execute()
            
            # Return True if user exists, False otherwise
            if response.data and len(response.data) > 0:
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to check user: {str(e)}")
    
    def get_user(self, username: str):
        """Get user details"""
        try:
            response = self.client.table("book_app_users")\
                .select("*")\
                .eq("username", username)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")
    
    def get_user_by_email(self, email: str):
        """Get user by email"""
        try:
            response = self.client.table("book_app_users")\
                .select("*")\
                .eq("email", email)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise Exception(f"Failed to get user by email: {str(e)}")
    
    def delete_user(self, username: str):
        """Delete a user"""
        try:
            response = self.client.table("book_app_users")\
                .delete()\
                .eq("username", username)\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to delete user: {str(e)}")
    
    def get_all_users(self):
        """Get all users"""
        try:
            response = self.client.table("book_app_users")\
                .select("*")\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get all users: {str(e)}")

    #----------- user_books functions -----------------#
    def add_user_book(self, username: str, book_name: str, book_id: str):
        """Add a book to a user's collection"""
        try:
            data = {
                "username": username,
                "book_id": book_id,
                "book_name": book_name
            }
            response = self.client.table("user_books").insert(data).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to add book: {str(e)}")
    
    def get_user_books(self, username: str):
        """Get all books for a user"""
        try:
            response = self.client.table("user_books")\
                .select("book_name")\
                .eq("username", username)\
                .execute()
            return [book["book_name"] for book in response.data]
        except Exception as e:
            raise Exception(f"Failed to get user books: {str(e)}")
    
    def get_user_book_ids(self, username: str):
        """Get all book IDs for a user"""
        try:
            response = self.client.table("user_books")\
                .select("book_id")\
                .eq("username", username)\
                .execute()
            return [book["book_id"] for book in response.data]
        except Exception as e:
            raise Exception(f"Failed to get user book IDs: {str(e)}")
    
    def delete_user_book(self, username: str, book_name: str):
        """Delete a book from user's collection"""
        try:
            # First get the book_id
            response = self.client.table("user_books")\
                .select("book_id")\
                .eq("username", username)\
                .eq("book_name", book_name)\
                .execute()
            
            if not response.data:
                raise Exception("Book not found")
            
            book_id = response.data[0]["book_id"]
            
            # Delete the book
            self.client.table("user_books")\
                .delete()\
                .eq("username", username)\
                .eq("book_name", book_name)\
                .execute()
            
            return book_id
        except Exception as e:
            raise Exception(f"Failed to delete book: {str(e)}")
    
    #----------- user_blog functions -----------------#
    def add_user_blog(self, username: str, book_id: str, title: str, 
                     description: str, subject_places: str, subject_times: str, 
                     subjects: str, thoughts: str):
        """Add or update a blog entry for a user's book"""
        try:
            data = {
                "username": username,
                "book_id": book_id,
                "title": title,
                "description": description,
                "subject_places": subject_places,
                "subject_times": subject_times,
                "subjects": subjects,
                "thoughts": thoughts
            }
            
            # Check if blog already exists
            existing = self.client.table("user_blogs")\
                .select("*")\
                .eq("username", username)\
                .eq("book_id", book_id)\
                .execute()
            
            if existing.data:
                # Update existing blog
                response = self.client.table("user_blogs")\
                    .update(data)\
                    .eq("username", username)\
                    .eq("book_id", book_id)\
                    .execute()
            else:
                # Insert new blog
                response = self.client.table("user_blogs")\
                    .insert(data)\
                    .execute()
            
            return response.data
        except Exception as e:
            raise Exception(f"Failed to add blog: {str(e)}")
    
    def get_user_blog(self, username: str, book_id: str):
        """Get a specific blog entry"""
        try:
            response = self.client.table("user_blogs")\
                .select("*")\
                .eq("username", username)\
                .eq("book_id", book_id)\
                .execute()
            
            if not response.data:
                return None
            
            return response.data[0]
        except Exception as e:
            raise Exception(f"Failed to get blog: {str(e)}")
    
    def delete_user_blog(self, username: str, book_id: str):
        """Delete a blog entry"""
        try:
            response = self.client.table("user_blogs")\
                .delete()\
                .eq("username", username)\
                .eq("book_id", book_id)\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to delete blog: {str(e)}")

# Create a singleton instance
supabase_service = SupabaseService()