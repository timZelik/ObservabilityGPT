import logging

import requests

key = "" #paste API key into double quotes
appId = "" #paste API appID into double quotes
api_url = f"" #paste API url with appId within the {} in the apps directory


def call_api(query):
    # query = "traces | take 10"
    query_params = {"query": query}
    headers = {"x-api-key": key}
    response = requests.get(api_url, params=query_params, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("HTTP error occurred: ", err)
        print("The query that caused the error: ", query)
    except Exception as err:
        print("Other error occurred: ", err)
    else:
        return response.json()
