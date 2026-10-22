"""Closed response schema: unknown source fields never become public DTO fields."""
from pydantic import BaseModel, ConfigDict


class DTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Media(DTO):
    media_id: str
    sha256: str
    bytes: int
    format: str
    storage: str


class Drawing(DTO):
    id: str
    title: str
    media: Media | None


class Document(DTO):
    title: str
    media: Media


class Version(DTO):
    version: str
    state: str
    verdict: str
    drawings: list[Drawing]
    video: Media | None
    documents: list[Document]


class Asset(DTO):
    id: str
    title: str
    project: str
    version: str
    state: str
    approval: str
    source: str
    review: str
    media: Media | None
    availability: str


class Project(DTO):
    id: str
    title: str
    state: str


class History(DTO):
    date: str | None
    note: str


class Review(DTO):
    id: str
    version: str
    verdict: str
    scope: str
    video_scope: str
    date: str | None
    actor: str
    reason: str
    keys: dict[str, str]
    next_actions: list[str]


class Cut(DTO):
    id: str
    episode: str
    title: str
    purpose: str
    stage: str
    verdict: str
    latest: str | None
    next_stage_allowed: bool
    producer_approval: str
    versions: list[Version]


class StudioIndex(DTO):
    schema_version: int
    revision: int
    source_sha256: str
    imported_at: str
    disclosure: str
    mode: str
    projects: list[Project]
    assets: list[Asset]
    history: list[History]
    cuts: list[Cut]
    reviews: list[Review]
