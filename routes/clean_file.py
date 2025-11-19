from fastapi import APIRouter
import os

router = APIRouter(
    prefix='/clean_files',
    tags=['clean_files']
)

@router.get('/clean_files')
def clean_files():
    clean_folder(folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mp3"))
    clean_folder(folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pdf"))

def clean_folder(folder_path):

    """Deletes all files in the folder if there are more than 2."""
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return
    
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    if len(files) > 2:
        for file in files:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)
            print(f"Deleted: {file_path}")
    else:
        print("Less than or equal to 2 files, no deletion performed.")