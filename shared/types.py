from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SentimentLabel(Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class EntityType(Enum):
    CRYPTO = "CRYPTO"
    EXCHANGE = "EXCHANGE"
    PERSON = "PERSON"
    REGULATORY_BODY = "REGULATORY_BODY"
    EVENT = "EVENT"


class DocumentSource(Enum):
    WHITEPAPER = "whitepaper"
    REGULATORY = "regulatory"
    MARKET_DATA = "market_data"
    CASE_STUDY = "case_study"
    SOCIAL_MEDIA = "social_media"
    NEWS = "news"


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Conversation:
    id: str
    messages: list[ChatMessage] = field(default_factory=list)


@dataclass
class SentimentResult:
    label: str
    confidence: float
    scores: dict[str, float]


@dataclass
class GenerationResult:
    text: str
    model_name: str


@dataclass
class RetrievedDocument:
    title: str
    content: str
    source: str
    relevance_score: float
    metadata: dict


@dataclass
class RetrievalResult:
    query: str
    documents: list[RetrievedDocument]
    total_candidates: int
    retrieval_time_ms: float


@dataclass
class Entity:
    text: str
    type: str
    start: int
    end: int
    confidence: float

