from content.edx_content_manager import EdxContentManager


# Create your views here.
async def get_learning_objectives(request, block_id=None):
    """
    Async Django view to get vertical blocks for a specified block ID

    Args:
        request: The HTTP request
        block_id: The EdX block ID

    Returns:
        JsonResponse with the vertical blocks data
    """
    if not block_id:
        block_id = request.GET.get("block_id")

    if not block_id:
        return JsonResponse({"error": "Block ID is required"}, status=400)

    # Get the EdX client and fetch course blocks
    async with OAuthClient(service_type="OPENEDX") as client:
        edx_client = EdxClient(client=client)
        blocks_data = await edx_client.get_course_blocks(block_id)

    if not blocks_data or "blocks" not in blocks_data:
        return JsonResponse(
            [],
            status=404,
        )

    # Extract only vertical blocks
    vertical_blocks = []

    for block_id, block_data in blocks_data["blocks"].items():
        if block_data.get("type") == "vertical":
            vertical_block = {
                "name": block_data.get("display_name", "Untitled"),
                "iframe_id": block_data.get("id"),
            }
            vertical_blocks.append(vertical_block)

    if not vertical_blocks:
        return JsonResponse(
            [],
            status=404,
        )

    return JsonResponse(vertical_blocks, safe=False)


async def get_edx_resources(request, block_id):
    """
    Async Django view to get EdX resources (HTML, PDF, Video) for a block ID

    Args:
        request: The HTTP request
        block_id: The EdX block ID

    Returns:
        JsonResponse with the content data
    """
    ordered = request.GET.get("ordered", "false").lower() == "true"

    # TODO : this is a bottle neck--> creating new connections on every new request
    # Use pooling
    # Get the EdX client and fetch course blocks
    async with OAuthClient(service_type="OPENEDX") as client:
        edx_client = EdxClient(client=client)
        blocks_data = await edx_client.get_course_blocks(block_id)

    content_manager = EdxContentManager(blocks_data)

    if not content_manager.valid:
        return JsonResponse(
            {
                "success": False,
                "message": "No content found",
                "content": {"html": [], "pdf": [], "video": []} if not ordered else [],
                "counts": {"html": 0, "pdf": 0, "video": 0},
            }
        )

    if ordered:
        content = content_manager.format_ordered_content()
    else:
        content = content_manager.format_categorized_content()

    counts = content_manager.get_content_counts(content)

    result = {
        "success": True,
        "block_id": block_id,
        "content": content,
        "counts": counts,
    }

    return JsonResponse(result)
