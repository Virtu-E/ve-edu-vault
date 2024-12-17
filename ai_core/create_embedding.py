#!/bin/env python3
import requests
from requests.exceptions import ConnectionError


def get_embedding(query_str, api_key):
    """
    Retrieves the embedding for a given plot
    """
    # TODO: Create a variable, `endpoint`, and set it to the Open AI vector embeddings API endpoint
    endpoint = "https://api.openai.com/v1/embeddings"
    # TODO: For the value of `Authorization`, set it to a string that includes the `api_key` variable. For example, "Bearer {api_key}"
    headers = {
        "Authorization": "Bearer 3fe4ffef44fp_049",
        "Content-Type": "application/json",
    }
    payload = {
        # TODO: Define the model to use and set the input field to the variable`query_str`
        "model": "text-embedding-ada-002",
        "input": query_str,
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        if response.status_code == 404:
            print(f"No embedding found for plot: {query_str}")
            return None
        elif response.status_code != 200:
            print("Failed to get embedding")
            response.raise_for_status()

        # Extract the embedding from the response
        response_json = response.json()
        first_item = response_json[0] if response_json else {}
        data_field = first_item.get("data", [{}])
        first_data_item = data_field[0] if data_field else {}
        embedding = first_data_item.get("embedding", None)
        return embedding
    except ConnectionError:
        print("Error connecting to the API server")
        return None
    except Exception as error:
        print("Failed to get embedding")
        print(error)
        return None
