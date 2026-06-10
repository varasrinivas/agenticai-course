from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=List[schemas.Tag])
def list_tags(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Tag).order_by(models.Tag.name).all()


@router.post("/", response_model=schemas.Tag, status_code=201)
def create_tag(
    tag: schemas.TagCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    if db.query(models.Tag).filter(models.Tag.name == tag.name).first():
        raise HTTPException(status_code=400, detail="Tag name already exists")
    db_tag = models.Tag(name=tag.name, color=tag.color)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


@router.delete("/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
