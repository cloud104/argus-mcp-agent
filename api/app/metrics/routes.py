"""
Metrics routes - Provides log statistics and metrics aggregations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime, timedelta
import os
from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv

from app.auth.dependencies import get_current_user
from app.auth.models import User

load_dotenv()

router = APIRouter(prefix="/metrics", tags=["Metrics"])

ES_HOST = os.getenv("ES_HOST")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_TIMEOUT = int(os.getenv("ES_TIMEOUT", "30"))

_es: AsyncElasticsearch | None = None

async def get_es() -> AsyncElasticsearch:
    """Get or create Elasticsearch client"""
    global _es
    if _es is None:
        _es = AsyncElasticsearch(
            ES_HOST,
            basic_auth=(ES_USER, ES_PASSWORD),
            verify_certs=False,
            request_timeout=ES_TIMEOUT,
        )
    return _es


@router.get("/dashboard")
async def get_dashboard_metrics(
    index: str = "csalva7_203089_logs",
    window: str = "7d",
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated metrics for dashboard visualization.

    Returns:
    - total_logs: Total number of logs in window
    - severity_distribution: Count by severity level
    - appname_distribution: Count by application name
    - hourly_distribution: Logs per hour
    - top_hosts: Top 5 hosts by log count
    - error_rate: Percentage of errors and warnings
    """
    try:
        es = await get_es()

        # Build query for time range
        now = datetime.utcnow()
        if window.endswith('h'):
            hours = int(window[:-1])
            start_time = now - timedelta(hours=hours)
        elif window.endswith('d'):
            days = int(window[:-1])
            start_time = now - timedelta(days=days)
        else:
            # Default to 7 days
            start_time = now - timedelta(days=7)

        # Main aggregation query
        query = {
            "query": {
                "range": {
                    "timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": now.isoformat()
                    }
                }
            },
            "size": 0,
            "aggs": {
                "severity_agg": {
                    "terms": {
                        "field": "severity.keyword",
                        "size": 10
                    }
                },
                "appname_agg": {
                    "terms": {
                        "field": "appname.keyword",
                        "size": 10
                    }
                },
                "host_agg": {
                    "terms": {
                        "field": "host.keyword",
                        "size": 5
                    }
                },
                "hourly_agg": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": "1h",
                        "format": "yyyy-MM-dd'T'HH:mm:ss"
                    }
                }
            }
        }

        # Execute query
        response = await es.search(index=index, body=query)

        # Extract aggregations
        aggs = response.get("aggregations", {})
        total_logs = response.get("hits", {}).get("total", {}).get("value", 0)

        # Process severity distribution
        severity_buckets = aggs.get("severity_agg", {}).get("buckets", [])
        severity_dist = {
            bucket["key"]: bucket["doc_count"]
            for bucket in severity_buckets
        }

        # Process appname distribution
        appname_buckets = aggs.get("appname_agg", {}).get("buckets", [])
        appname_dist = {
            bucket["key"]: bucket["doc_count"]
            for bucket in appname_buckets
        }

        # Process top hosts
        host_buckets = aggs.get("host_agg", {}).get("buckets", [])
        top_hosts = [
            {"host": bucket["key"], "count": bucket["doc_count"]}
            for bucket in host_buckets
        ]

        # Process hourly distribution
        hourly_buckets = aggs.get("hourly_agg", {}).get("buckets", [])
        hourly_dist = [
            {"timestamp": bucket["key_as_string"], "count": bucket["doc_count"]}
            for bucket in hourly_buckets
        ]

        # Calculate error rate (case-insensitive keys)
        lower_map = {k.lower(): v for k, v in severity_dist.items()}
        errors = lower_map.get("error", 0) + lower_map.get("fatal", 0) + lower_map.get("critical", 0) + lower_map.get("emerg", 0)
        warnings = lower_map.get("warning", 0)
        error_rate = ((errors + warnings) / total_logs * 100) if total_logs > 0 else 0

        return {
            "total_logs": total_logs,
            "severity_distribution": severity_dist,
            "appname_distribution": appname_dist,
            "top_hosts": top_hosts,
            "hourly_distribution": hourly_dist,
            "error_rate": round(error_rate, 2),
            "window": window,
            "period": {
                "start": start_time.isoformat(),
                "end": now.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch metrics: {str(e)}"
        )
