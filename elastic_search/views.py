from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from elasticsearch_dsl import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from course_ware.documents import TopicDocument

# Constants
# CACHE_TTL = getattr(settings, 'SEARCH_CACHE_TTL', 300)  # 5 minutes default
MAX_PAGE_SIZE = getattr(settings, "MAX_SEARCH_PAGE_SIZE", 100)
DEFAULT_PAGE_SIZE = 10
# TODO Boosting topic name relevance
# Define searchable fields mapping
SEARCHABLE_FIELDS = {
    "topic": "topic_name",
    "course": "course_name",
    "objective": "learning_objectives.name",
    "metadata": "metadata",
}


class SearchQueryBuilder:
    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.search = TopicDocument.search()
        self.queries = []

    def build_pagination(self) -> None:
        """Handle pagination with validation"""
        try:
            self.page = max(1, int(self.params.get("page", 1)))
            self.size = min(
                MAX_PAGE_SIZE, max(1, int(self.params.get("size", DEFAULT_PAGE_SIZE)))
            )
        except ValueError:
            self.page = 1
            self.size = DEFAULT_PAGE_SIZE

    def build_queries(self) -> None:
        """Build search queries based on parameters"""
        for param, value in self.params.items():
            if not value or param in ("page", "size"):
                continue

            if param == "objective":
                self.queries.append(
                    Q(
                        "nested",
                        path="learning_objectives",
                        inner_hits={},
                        query=Q(
                            "bool",
                            should=[
                                Q(
                                    "match_phrase_prefix",
                                    **{
                                        "learning_objectives.name": {
                                            "query": value,
                                            "max_expansions": 50,
                                            "boost": 2.0,
                                        }
                                    },
                                ),
                                Q(
                                    "wildcard",
                                    **{"learning_objectives.name": f"*{value}*"},
                                ),
                                Q(
                                    "match",
                                    **{
                                        "learning_objectives.name": {
                                            "query": value,
                                            "fuzziness": "AUTO",
                                        }
                                    },
                                ),
                            ],
                            minimum_should_match=1,
                        ),
                    )
                )

            elif param in SEARCHABLE_FIELDS:
                field = SEARCHABLE_FIELDS[param]
                self.queries.append(
                    Q("match", **{field: {"query": value, "fuzziness": "AUTO"}})
                )
            elif param.endswith("_id"):
                self.search = self.search.filter("term", **{param: value})

    def get_search_query(self) -> TopicDocument:
        """Combine all queries and return final search object"""
        if self.queries:
            self.search = self.search.query(
                Q("bool", should=self.queries, minimum_should_match=1)
            )

        start = (self.page - 1) * self.size
        return self.search[start: start + self.size]



# @lru_cache(maxsize=128) TODO : implement cache system
def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Retrieve cached search results"""
    return cache.get(cache_key)


def format_search_result(params, hit: Any) -> Dict[str, Any]:
    """Format individual search result"""
    matched_objectives = []

    # Only process inner_hits if we're searching by objective
    if "objective" in params and hasattr(hit.meta, "inner_hits"):
        for inner_hit in hit.meta.inner_hits["learning_objectives"].hits:
            matched_objectives.append(
                {
                    "name": inner_hit.name,
                    "id": inner_hit.id,
                    "description": inner_hit.description,
                }
            )
    else:
        # Return all objectives if not searching by objective
        matched_objectives = [
            {"name": obj.name, "id": obj.id, "description": obj.description}
            for obj in getattr(hit, "learning_objectives", [])
        ]

    return {
        "topic_name": hit.topic_name,
        "topic_id": hit.topic_id,
        "course_id": hit.course_id,
        "course_name": hit.course_name,
        "learning_objectives": matched_objectives,
        "metadata": hit.metadata.to_dict() if hasattr(hit, "metadata") else {},
        "_score": hit.meta.score,
    }


@api_view(["GET"])
def search_topics(request):
    """
    Search topics with caching and optimized query building.
    """
    try:
        # Build cache key from request parameters
        cache_key = f"topic_search:{hash(frozenset(request.GET.items()))}"
        cached_result = get_cached_result(cache_key)

        if cached_result:
            return Response(cached_result)

        # Build and execute search
        query_builder = SearchQueryBuilder(request.GET)
        query_builder.build_pagination()
        query_builder.build_queries()

        # Execute search with timeout
        response = query_builder.get_search_query().execute()

        # Format results
        results = [format_search_result(request.GET, hit) for hit in response]

        result_data = {
            "results": results,
            "total": response.hits.total.value,
            "page": query_builder.page,
            "size": query_builder.size,
            "took": response.took,  # Include query execution time
        }

        # Cache the results
        # cache.set(cache_key, result_data, CACHE_TTL) TODO : implement caching

        return Response(result_data)

    except ValueError as ve:
        return Response(
            {"error": "Invalid parameter value", "detail": str(ve)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": "Search operation failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
