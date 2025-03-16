from fastapi import APIRouter, Query
from functions.user_books import add_book_to_user, get_user_books_list, delete_book_user, get_user_book_ids

router = APIRouter(
    prefix='/user_book',
    tags=['user_book']
)

@router.post('/add_book_list')
def add_book_list(username, book, book_id):
    return add_book_to_user(username, book, book_id)

@router.get("/get_user_books_list")
def get_user_books(username: str):
    return get_user_books_list(username)


@router.delete("/delete_book/{username}")
def delete_book(username: str, book: str = Query(...)):
    return delete_book_user(username, book)

@router.get("/user_book_id/{username}")
def user_book_ids(username):
    return get_user_book_ids(username)



