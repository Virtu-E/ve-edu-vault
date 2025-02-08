from typing import Any, Dict

from elastic_search.api import DataFetcher
from elastic_search.operations import ElasticsearchOperations, Sync
from elastic_search.transformer import DataTransformer


class ElasticSearchSync(Sync):
    def __init__(
        self,
        data_fetcher: DataFetcher,
        data_transformer: DataTransformer,
        es_handler: ElasticsearchOperations,
    ):
        self.data_fetcher = data_fetcher
        self.data_transformer = data_transformer
        self.es_handler = es_handler

    def sync_data(self) -> Dict[str, Any]:
        try:
            # Fetch data
            raw_data = self.data_fetcher.fetch_data()

            # Transform data
            transformed_data = self.data_transformer.transform(
                raw_data["course_blocks"]
            )

            # Bulk update to Elasticsearch
            result = self.es_handler.bulk_update(transformed_data)

            return {"status": "success", "statistics": result}
        except Exception as e:
            raise e
            # return {"status": "error", "message": str(e)}
