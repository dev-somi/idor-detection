from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import FileRecord, User
from app.schemas import FileDownloadOut, FileOut
router = APIRouter(tags=['files'])

@router.get('/files/{file_id}/download', response_model=FileDownloadOut)
def download_file(file_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    file_record = db.get(FileRecord, file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail='File not found')
    return file_record

@router.get('/me/files', response_model=list[FileOut])
def get_my_files(current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    files = db.query(FileRecord).filter(FileRecord.owner_id == current_user.id).all()
    return files
