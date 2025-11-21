from fastapi import APIRouter, Query, Depends
from functions.user_books import add_book_to_user, get_user_books_list, delete_book_user, get_user_book_ids
from helper.authentication import APIKeyChecker

router = APIRouter(
    prefix='/user_book',
    tags=['user_book']
)

# API key checker for user book operations
user_book_auth = APIKeyChecker("user_book")

@router.post('/add_book_list')
def add_book_list(
    username: str, 
    book: str, 
    book_id: str,
    api_key: str = Depends(user_book_auth)
):
    return add_book_to_user(username, book, book_id)

@router.get("/get_user_books_list")
def get_user_books(
    username: str,
    api_key: str = Depends(user_book_auth)
):
    return get_user_books_list(username)

@router.delete("/delete_book/{username}")
def delete_book(
    username: str, 
    book: str = Query(...),
    api_key: str = Depends(user_book_auth)
):
    return delete_book_user(username, book)

@router.get("/user_book_id/{username}")
def user_book_ids(
    username: str,
    api_key: str = Depends(user_book_auth)
):
    return get_user_book_ids(username)