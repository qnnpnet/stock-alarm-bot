from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class NewsArticle(BaseModel):
    title: str
    link: str
    content: str
    published: Optional[datetime]
