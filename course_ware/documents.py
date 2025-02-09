from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from course_ware.models import Category, Topic

# TODO : add support for academic level filtering
# TODO : add support for images and maybe even some AI input ?


@registry.register_document
class TopicDocument(Document):
    topic_name = fields.TextField()
    topic_id = fields.KeywordField()
    course_id = fields.KeywordField()
    course_name = fields.TextField()

    learning_objectives = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "id": fields.KeywordField(),
        }
    )

    metadata = fields.ObjectField(
        properties={
            "created_at": fields.DateField(),
            "updated_at": fields.DateField(),
        }
    )

    class Index:
        name = "topics"
        settings = {"number_of_shards": 1, "number_of_replicas": 1}

    class Django:
        model = Category
        related_models = [Topic]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Category):
            return related_instance.topics.all()

    def prepare(self, instance):
        # Get all topics related to this category
        topics = instance.topics.all()

        # Create learning objectives list from topics
        learning_objectives = [
            {"name": topic.name, "id": topic.block_id} for topic in topics
        ]

        data = {
            "topic_name": instance.name,
            "topic_id": instance.block_id,
            "course_id": instance.course.course_key,
            "course_name": instance.course.name,
            "learning_objectives": learning_objectives,
            "metadata": {
                "created_at": instance.created_at,
                "updated_at": instance.updated_at,
            },
        }
        return data
