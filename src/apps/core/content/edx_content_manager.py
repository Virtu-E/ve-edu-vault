import logging

logger = logging.getLogger(__name__)


class EdxContentManager:
    """
    Class for managing and formatting EdX content blocks.

    This class processes raw blocks data from EdX and provides methods
    to format and categorize content by type.

    Attributes:
        blocks_data (dict): Raw data containing EdX content blocks
        valid (bool): Whether the blocks_data is valid and contains blocks
    """

    def __init__(self, blocks_data):
        """
        Initialize the EdX content manager.

        Args:
            blocks_data (dict): The raw blocks data from EdX
        """
        self.blocks_data = blocks_data
        self.valid = blocks_data and "blocks" in blocks_data
        if not self.valid:
            logger.warning("Invalid blocks data provided to EdxContentManager")

    def format_ordered_content(self):
        """
        Returns blocks in their original order, including only html, pdf and video blocks.

        Returns:
            list: Ordered list of simplified block data dictionaries
        """
        if not self.valid:
            logger.debug("Cannot format ordered content: invalid blocks data")
            return []

        ordered_blocks = []
        logger.debug(
            f"Processing {len(self.blocks_data['blocks'])} blocks for ordered content"
        )

        for block_id, block_data in self.blocks_data["blocks"].items():
            block_type = block_data.get("type")

            # Only include html, pdf, and video blocks
            if block_type in ["html", "pdf", "video"]:
                simplified_block = {
                    "name": block_data.get("display_name", "Untitled"),
                    "iframe_id": block_data.get("id"),
                    "type": block_type,
                }
                ordered_blocks.append(simplified_block)

        logger.debug(f"Returning {len(ordered_blocks)} ordered blocks")
        return ordered_blocks

    def format_categorized_content(self):
        """
        Returns blocks categorized by type (html, pdf, video).

        Returns:
            dict: Dictionary with keys 'html', 'pdf', 'video', each containing a list of blocks
        """
        if not self.valid:
            logger.debug("Cannot format categorized content: invalid blocks data")
            return {"html": [], "pdf": [], "video": []}

        html_blocks = []
        pdf_blocks = []
        video_blocks = []

        logger.debug(f"Categorizing {len(self.blocks_data['blocks'])} blocks by type")

        for block_id, block_data in self.blocks_data["blocks"].items():
            block_type = block_data.get("type")

            # Create a simplified version of the block data
            simplified_block = {
                "id": block_id,
                "block_id": block_id,
                "display_name": block_data.get("display_name", "Untitled"),
                "type": block_type,
            }

            # Sort by content type
            if block_type == "html":
                # Mark as study notes if relevant
                display_name = simplified_block["display_name"].lower()
                simplified_block["is_study_notes"] = (
                    "study" in display_name or "notes" in display_name
                )
                html_blocks.append(simplified_block)
            elif block_type == "pdf":
                pdf_blocks.append(simplified_block)
            elif block_type == "video":
                video_blocks.append(simplified_block)

        result = {
            "html": html_blocks,
            "pdf": pdf_blocks,
            "video": video_blocks,
        }

        logger.debug(
            f"Categorized blocks: {len(html_blocks)} HTML, {len(pdf_blocks)} PDF, {len(video_blocks)} video"
        )
        return result

    def get_content_counts(self, content):
        """
        Returns count of each content type.

        Args:
            content (list or dict): Content blocks, either as a list (ordered)
                                    or dict (categorized)

        Returns:
            dict: Dictionary with counts for each content type
        """
        if isinstance(content, list):
            # For ordered content, count by type
            counts = {"html": 0, "pdf": 0, "video": 0}
            for block in content:
                block_type = block.get("type")
                if block_type in counts:
                    counts[block_type] += 1
            logger.debug(f"Content counts from list: {counts}")
            return counts
        else:
            # For categorized content
            counts = {
                "html": len(content["html"]),
                "pdf": len(content["pdf"]),
                "video": len(content["video"]),
            }
            logger.debug(f"Content counts from dict: {counts}")
            return counts
