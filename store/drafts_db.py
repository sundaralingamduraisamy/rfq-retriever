from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import datetime

class Draft(SQLModel, table=True):
    id:int = Field(default=None, primary_key=True)
    content:str
    meta:str
    created_at:datetime = Field(default_factory=datetime.utcnow)

engine=create_engine("sqlite:///drafts.db")
SQLModel.metadata.create_all(engine)

def save_draft(content,meta):
    with Session(engine) as s:
        d=Draft(content=content,meta=meta)
        s.add(d)
        s.commit()
        return d.id
