"""
Resilience utilities for retry policies and error handling.

Este módulo fornece decorators e utilitários para implementar
padrões de resiliência como retry com backoff exponencial.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

logger = logging.getLogger(__name__)

# Retry decorator para operações de Elasticsearch
elasticsearch_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Retry decorator para operações HTTP genéricas
http_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Retry decorator para operações de banco de dados (ChromaDB, etc)
db_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type((ConnectionError, Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
