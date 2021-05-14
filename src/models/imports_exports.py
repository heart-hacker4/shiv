from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel


class GeneralData(BaseModel):
    sophie_version: str
    sophie_id: int
    version: int


class ExportInfo(BaseModel):
    chat_name: str
    chat_id: int
    date: datetime


class ExportModel(BaseModel):
    export_info: ExportInfo
    modules: dict
    general: GeneralData

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }
