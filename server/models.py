"""
Pydantic models for server API requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class TranslateAndSpeakRequest(BaseModel):
    """Request model for /translate_and_speak endpoint."""
    text: str = Field(..., description="English or mixed English-Chinese text to translate and speak")
    return_audio: bool = Field(default=False, description="If true, return WAV audio bytes instead of playing")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "The feature is complete. Ready for testing.",
                "return_audio": False
            }
        }


class TranslateAndSpeakResponse(BaseModel):
    """Response model for /translate_and_speak endpoint."""
    status: str = Field(..., description="Request status (queued/played/generated)")
    message: Optional[str] = Field(None, description="Status message")
    queue_position: Optional[int] = Field(None, description="Position in translation queue")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "queued",
                "message": "Request queued for translation",
                "queue_position": 1
            }
        }
