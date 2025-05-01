class EdxContentManager:
    """
    Class for managing and formatting EdX content blocks
    """

    def __init__(self, blocks_data):
        self.blocks_data = blocks_data
        self.valid = blocks_data and "blocks" in blocks_data

    def format_ordered_content(self):
        """
        Returns blocks in their original order, including only html, pdf and video blocks
        """
        if not self.valid:
            return []

        ordered_blocks = []

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

        return ordered_blocks

    def format_categorized_content(self):
        """
        Returns blocks categorized by type (html, pdf, video)
        """
        if not self.valid:
            return {"html": [], "pdf": [], "video": []}

        html_blocks = []
        pdf_blocks = []
        video_blocks = []

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

        return {
            "html": html_blocks,
            "pdf": pdf_blocks,
            "video": video_blocks,
        }

    def get_content_counts(self, content):
        """
        Returns count of each content type
        """
        if isinstance(content, list):
            # For ordered content, count by type
            counts = {"html": 0, "pdf": 0, "video": 0}
            for block in content:
                block_type = block.get("type")
                if block_type in counts:
                    counts[block_type] += 1
            return counts
        else:
            # For categorized content
            return {
                "html": len(content["html"]),
                "pdf": len(content["pdf"]),
                "video": len(content["video"]),
            }
