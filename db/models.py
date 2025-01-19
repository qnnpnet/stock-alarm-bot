from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Alert(BaseModel):
    symbol: str
    alert_type: str
    price: float
    timestamp: datetime


class WatchedKeyword(BaseModel):
    keyword: str
    last_check: datetime


class Portfolio(BaseModel):
    ticker: str
    quantity: int
