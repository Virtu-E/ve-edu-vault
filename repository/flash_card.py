from abc import ABC, abstractmethod
from typing import List

from data_types.flash_cards import FlashCardQuestion


class FlashCardRepositoryInterface(ABC):

    @abstractmethod
    def get_card_collection(self, query) -> List[FlashCardQuestion]:
        raise NotImplementedError()


class FlashCardRepository(FlashCardRepositoryInterface):
    def __init__(
        self,
        database_name: str,
        collection_name: str,
        database_engine,
    ):
        self._database_name = database_name
        self._collection_name = collection_name
        self._database_engine = database_engine

    def get_card_collection(self, query) -> List[FlashCardQuestion]:
        docs = self._database_engine.fetch_from_db(
            self._database_name, self._collection_name, query
        )
        return [
            FlashCardQuestion(**{**question, "_id": str(question["_id"])}).model_dump()
            for question in docs
        ]


class FlashCardRepoFactory:
    @staticmethod
    def create_repository(collection_name: str) -> FlashCardRepositoryInterface:
        return FlashCardRepository(
            database_name="flashcards",
            collection_name=collection_name,
            database_engine={},
        )
