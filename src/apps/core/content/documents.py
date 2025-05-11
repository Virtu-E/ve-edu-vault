from django_elasticsearch_dsl import Document, fields

from .models import Topic, SubTopic


# TODO : add support for academic level filtering
# TODO : add support for images and maybe even some AI input ?

# need to exclude the below from running when testing


# @registry.register_document
class SubTopicDocument(Document):
    sub_topic_name = fields.TextField()
    sub_topic_id = fields.KeywordField()
    course_id = fields.KeywordField()
    course_name = fields.TextField()

    sub_topics = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "id": fields.KeywordField(),
            "description": fields.TextField(),
        }
    )

    metadata = fields.ObjectField(
        properties={
            "created_at": fields.DateField(),
            "updated_at": fields.DateField(),
        }
    )

    class Index:
        name = "sub_topics"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Topic
        related_models = [SubTopic]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Topic):
            return related_instance.topics.all()

    def prepare(self, instance):
        # Get all topics related to this category
        sub_topics = instance.topics.all()

        # Create learning objectives list from topics
        sub_topics = [
            {
                "name": data.name,
                "id": data.block_id,
                "description": data.flash_card_description,
            }
            for data in sub_topics
        ]

        data = {
            "topic_name": instance.name,
            "topic_id": instance.block_id,
            "course_id": instance.course.course_key,
            "course_name": instance.course.name,
            "sub_topics": sub_topics,
            "metadata": {
                "created_at": instance.created_at,
                "updated_at": instance.updated_at,
            },
        }
        return data
