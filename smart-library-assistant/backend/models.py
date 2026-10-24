
from pydantic import BaseModel, Field, model_validator


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    isbn: str | None = None
    description: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    edition: str | None = None
    language: str = "English"
    cover_image_url: str | None = None
    total_copies: int = Field(default=1, ge=0)
    available_copies: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_copies(self):
        if self.available_copies is None:
            self.available_copies = self.total_copies
        if self.available_copies > self.total_copies:
            raise ValueError("Available copies cannot exceed total copies")
        return self


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    isbn: str | None = None
    description: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    edition: str | None = None
    language: str | None = None
    cover_image_url: str | None = None
    total_copies: int | None = Field(default=None, ge=0)
    available_copies: int | None = Field(default=None, ge=0)
