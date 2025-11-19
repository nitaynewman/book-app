from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from functions.user_blog import add_blog_user, get_user_blog, delete_user_blog
from typing import Any

router = APIRouter(
    prefix='/blog',
    tags=['blog']
)
class BlogRequest(BaseModel):
    title: Any
    description: Any
    subject_places: Any
    subject_times: Any
    subjects: Any
    book_id: Any
    thoughts: Any

@router.post('/add_blog/{username}')
async def add_blog(username: str, blog_data: BlogRequest):
    try:
        return add_blog_user(
            username, 
            blog_data.title, 
            blog_data.description, 
            blog_data.subject_places, 
            blog_data.subject_times, 
            blog_data.subjects, 
            blog_data.book_id, 
            blog_data.thoughts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get('/get_blog/{username}/{book_id}')
def get_blog(username: str, book_id: str):
    return get_user_blog(username, book_id)

@router.delete('/delete_blog/{username}/{book_id}')
def delete_blog(username: str, book_id: str):
    return delete_user_blog(username, book_id)