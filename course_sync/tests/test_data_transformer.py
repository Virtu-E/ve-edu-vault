"""
Tests for ai_core.course_sync.data_transformer
"""

from course_sync.data_transformer import EdxDataTransformer
from course_sync.data_types import CourseStructure, EdxCourseOutline, Topic
from course_sync.tests.factories import CourseStructureFactory


class TestEdxDataTransformer:
    """Test cases for EdxDataTransformer class"""

    def test_transform_structure_empty_data(self):
        """Test transforming empty structure data"""
        empty_structure = {}
        result = EdxDataTransformer.transform_structure(empty_structure)

        assert isinstance(result, CourseStructure)
        assert len(result.topics) == 0
        assert len(result.sub_topics) == 0
        assert len(result.topic_to_sub_topic) == 0

    def test_transform_structure_with_data(self):
        """Test transforming structure with actual data"""
        # Create test data with known IDs
        topic_id = "topic-123"
        subtopic_id = "subtopic-456"

        structure = {
            "course_structure": {
                "child_info": {
                    "children": [
                        {
                            "id": topic_id,
                            "has_children": True,
                            "child_info": {"children": [{"id": subtopic_id}]},
                        }
                    ]
                }
            }
        }

        result = EdxDataTransformer.transform_structure(structure)

        assert isinstance(result, CourseStructure)
        assert topic_id in result.topics
        assert subtopic_id in result.sub_topics
        assert result.topic_to_sub_topic[subtopic_id] == topic_id

    def test_transform_structure_with_factory_data(self):
        """Test transform_structure with factory-generated data"""
        structure = CourseStructureFactory()
        result = EdxDataTransformer.transform_structure(structure)

        # Get expected values from factory data
        topics_set = set()
        sub_topics_set = set()
        topic_to_sub_topic = {}

        for topic in structure["course_structure"]["child_info"]["children"]:
            topic_id = topic.get("id")
            if topic_id:
                topics_set.add(topic_id)

            for sub_topic in topic.get("child_info", {}).get("children", []):
                sub_topic_id = sub_topic.get("id")
                if sub_topic_id:
                    sub_topics_set.add(sub_topic_id)
                    topic_to_sub_topic[sub_topic_id] = topic_id

        assert result.topics == topics_set
        assert result.sub_topics == sub_topics_set
        assert result.topic_to_sub_topic == topic_to_sub_topic

    def test_transform_topics_empty_data(self):
        """Test transforming empty topics data"""
        empty_structure = {}
        result = EdxDataTransformer.transform_topics(empty_structure)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_transform_topics_with_data(self):
        """Test transforming topics with actual data"""
        # Create test data with known values
        topic_id = "topic-abc"
        topic_name = "Test Topic"
        subtopic_id = "subtopic-xyz"
        subtopic_name = "Test Subtopic"

        structure = {
            "course_structure": {
                "child_info": {
                    "children": [
                        {
                            "id": topic_id,
                            "display_name": topic_name,
                            "has_children": True,
                            "child_info": {
                                "children": [
                                    {"id": subtopic_id, "display_name": subtopic_name}
                                ]
                            },
                        }
                    ]
                }
            }
        }

        result = EdxDataTransformer.transform_topics(structure)

        assert len(result) == 1
        assert isinstance(result[0], Topic)
        assert result[0].id == topic_id
        assert result[0].name == topic_name
        assert len(result[0].sub_topics) == 1
        assert result[0].sub_topics[0].id == subtopic_id
        assert result[0].sub_topics[0].name == subtopic_name
        assert result[0].sub_topics[0].topic_id == topic_id

    def test_transform_topics_with_factory_data(self):
        """Test transform_topics with factory-generated data"""
        structure = CourseStructureFactory()
        result = EdxDataTransformer.transform_topics(structure)

        # Verify topics match the input structure
        topic_data_list = structure["course_structure"]["child_info"]["children"]
        assert len(result) == len(topic_data_list)

        for i, topic in enumerate(result):
            topic_data = topic_data_list[i]
            assert topic.id == topic_data["id"]
            assert topic.name == topic_data["display_name"]

            # Verify subtopics
            subtopic_data_list = topic_data["child_info"]["children"]
            assert len(topic.sub_topics) == len(subtopic_data_list)

            for j, subtopic in enumerate(topic.sub_topics):
                subtopic_data = subtopic_data_list[j]
                assert subtopic.id == subtopic_data["id"]
                assert subtopic.name == subtopic_data["display_name"]
                assert subtopic.topic_id == topic_data["id"]

    def test_transform_to_course_outline(self):
        """Test transform_to_course_outline method"""
        structure = CourseStructureFactory()
        course_id = "course-123"
        title = "Test Course"

        result = EdxDataTransformer.transform_to_course_outline(
            structure, course_id, title
        )

        assert isinstance(result, EdxCourseOutline)
        assert result.course_id == course_id
        assert result.title == title
        assert isinstance(result.structure, CourseStructure)
        assert isinstance(result.topics, list)
        assert all(isinstance(topic, Topic) for topic in result.topics)

    def test_transform_to_course_outline_empty_data(self):
        """Test transform_to_course_outline with empty data"""
        empty_structure = {}
        course_id = "empty-course"
        title = "Empty Course"

        result = EdxDataTransformer.transform_to_course_outline(
            empty_structure, course_id, title
        )

        assert isinstance(result, EdxCourseOutline)
        assert result.course_id == course_id
        assert result.title == title
        assert isinstance(result.structure, CourseStructure)
        assert len(result.structure.topics) == 0
        assert len(result.structure.sub_topics) == 0
        assert len(result.structure.topic_to_sub_topic) == 0
        assert isinstance(result.topics, list)
        assert len(result.topics) == 0

    def test_structure_with_missing_data(self):
        """Test handling of missing data in structure"""
        # Structure with missing child_info
        structure = {
            "course_structure": {
                "some_other_field": "value"
                # No child_info field
            }
        }

        result = EdxDataTransformer.transform_structure(structure)
        assert len(result.topics) == 0
        assert len(result.sub_topics) == 0

        # Structure with topics missing IDs
        structure = {
            "course_structure": {
                "child_info": {
                    "children": [
                        {
                            # No ID field
                            "display_name": "Topic without ID",
                            "has_children": False,
                        }
                    ]
                }
            }
        }

        result = EdxDataTransformer.transform_structure(structure)
        assert len(result.topics) == 0

        # Structure with subtopics missing IDs
        structure = {
            "course_structure": {
                "child_info": {
                    "children": [
                        {
                            "id": "topic-with-invalid-subtopics",
                            "has_children": True,
                            "child_info": {
                                "children": [
                                    {
                                        # No ID field
                                        "display_name": "Subtopic without ID"
                                    }
                                ]
                            },
                        }
                    ]
                }
            }
        }

        result = EdxDataTransformer.transform_structure(structure)
        assert len(result.topics) == 1
        assert len(result.sub_topics) == 0
