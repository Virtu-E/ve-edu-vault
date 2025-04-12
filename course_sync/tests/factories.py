from factory import Factory, Faker
from factory.fuzzy import FuzzyText


class SubTopicDataFactory(Factory):
    """Factory for generating subtopic data dictionaries"""

    class Meta:
        model = dict

    id = FuzzyText(prefix="subtopic-")
    display_name = Faker("sentence", nb_words=3)
    has_children = False


class TopicDataFactory(Factory):
    """Factory for generating topic data dictionaries"""

    class Meta:
        model = dict

    id = FuzzyText(prefix="topic-")
    display_name = Faker("sentence", nb_words=4)
    has_children = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        children = []
        for _ in range(3):  # Create 3 sub-topics per topic
            children.append(SubTopicDataFactory())

        obj["child_info"] = {"children": children}
        return obj


class CourseStructureFactory(Factory):
    """Factory for generating course structure data dictionaries"""

    class Meta:
        model = dict

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        topics = []
        for _ in range(4):  # Create 4 topics
            topics.append(TopicDataFactory())

        obj["course_structure"] = {"child_info": {"children": topics}}
        return obj
