from elasticsearch import Elasticsearch


def test_elasticsearch_connection(es_url):
    """Test Elasticsearch connection and basic operations"""
    print("\n=== Elasticsearch Connection Test ===")
    print(f"Testing connection to: {es_url}")

    try:
        # Parse URL for potential auth
        auth = None

        # Initialize client
        print("\nInitializing Elasticsearch client...")
        es = Elasticsearch(
            [
                "https://d81dc60cb8b440b689c376163dfb471a.us-central1.gcp.cloud.es.io:443"
            ],
            api_key="YXZmaTVwUUJJTnJBNWlRcEY3bHA6dmozMFlXV3RTMzY3WjdaaGdqa0xpUQ==",
        )

        # Test 1: Basic Ping
        print("\nTest 1: Ping test...")
        if es.ping():
            print("✅ Ping successful")
        else:
            print("❌ Ping failed")

        # Test 2: Get cluster info
        print("\nTest 2: Getting cluster info...")
        info = es.info()
        print(f"✅ Connected to Elasticsearch cluster:")
        print(f"  - Version: {info['version']['number']}")
        print(f"  - Cluster name: {info['cluster_name']}")

        # Test 3: Check indices
        print("\nTest 3: Checking indices...")
        indices = es.indices.get_alias()
        print("✅ Found indices:", list(indices.keys()))

        print("\n✅ All connection tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Connection test failed:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return False


test_elasticsearch_connection(
    "https://fki4lsxch9:o30p2u5q55@virtueducate-search-1075195556.eu-central-1.bonsaisearch.net:443"
)
