"""OpenAI 임베딩 클라이언트."""

from __future__ import annotations

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from app.core.config import DisclosureConfig, get_config


EMBEDDING_BATCH_SIZE = 100


class EmbeddingError(RuntimeError):
    """임베딩 제공자 호출 실패."""


class EmbeddingRateLimitError(EmbeddingError):
    """OpenAI 요청 한도를 초과했다."""


class OpenAIEmbeddingClient:
    """동일 모델로 색인과 검색 질의를 임베딩한다."""

    def __init__(self, config: DisclosureConfig | None = None) -> None:
        self._config = config or get_config()
        self._config.validate_for_annual_report_search()
        self._client = OpenAI(api_key=self._config.openai_api_key)

    @property
    def model(self) -> str:
        assert self._config.embedding_model is not None
        return self._config.embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """입력 순서를 보존해 최대 100건씩 임베딩한다."""

        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise ValueError("빈 텍스트는 임베딩할 수 없습니다.")

        vectors: list[list[float]] = []
        for offset in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[offset : offset + EMBEDDING_BATCH_SIZE]
            try:
                response = self._client.embeddings.create(model=self.model, input=batch)
            except RateLimitError as error:
                raise EmbeddingRateLimitError("OpenAI 임베딩 호출 한도를 초과했습니다.") from error
            except (APIConnectionError, APITimeoutError, APIStatusError) as error:
                raise EmbeddingError("OpenAI 임베딩 호출에 실패했습니다.") from error
            vectors.extend(item.embedding for item in response.data)
        return vectors
