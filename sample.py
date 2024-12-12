import certifi
from pymongo import MongoClient

MONGO_URL = "mongodb+srv://myAtlasDBUser:tkB0QqcKTztNhnWW@myatlasclusteredu.2khcb.mongodb.net/?retryWrites=true&w=majority&appName=myAtlasClusterEDU"

client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())

try:
    database = client.get_database("sample_mflix")
    movies = database.get_collection("embedded_movies")

    # Query for a movie that has the title 'Back to the Future'
    query = {"title": "The Crowd Roars"}
    movie = movies.find_one(query)

    print(movie)

    client.close()

except Exception as e:
    raise Exception("Unable to find the document due to the following error: ", e)
