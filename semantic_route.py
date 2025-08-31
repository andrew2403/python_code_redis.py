import redis
from sentence_transformers import SentenceTransformer
import numpy as np

# 🔑 Redis connection (hard-coded)
REDIS_HOST = "redis-10609.re-cluster1.ps-redislabs.org"
REDIS_PORT = 10609
REDIS_PASSWORD = None   # or put your password if DB has one

# connect to Redis
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=False
)

# load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# define routes with reference exemplars
routes = {
    "GenAI programming topics": [
        "How does GPT work for coding?",
        "Explain embeddings in programming",
        "LangChain for developers",
        "Transformers in AI",
        "Vector databases for RAG"
    ],
    "Science fiction entertainment": [
        "I love watching Star Wars",
        "The Matrix movie is sci-fi",
        "Interstellar is a great film",
        "Reading Isaac Asimov books",
        "Dune is a classic science fiction novel"
    ],
    "Classical music": [
        "Play me some Mozart",
        "Beethoven symphonies are wonderful",
        "Bach wrote great compositions",
        "Classical violin concertos",
        "Opera and symphonies"
    ]
}

# create an index if not exists
def create_index():
    from redis.commands.search.field import VectorField, TagField, TextField
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType
    from redis.commands.search.client import Client

    index_name = "semantic_router_idx"
    client = Client(index_name, conn=redis_client)

    try:
        client.info()
        print("✅ Index already exists")
    except:
        schema = (
            TextField("route"),
            TextField("text"),
            VectorField("embedding",
                        "FLAT", {
                            "TYPE": "FLOAT32",
                            "DIM": 384,
                            "DISTANCE_METRIC": "COSINE"
                        })
        )
        client.create_index(schema, definition=IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH))
        print("✅ Created new index")

# store references
def store_references():
    dim = 384
    for route, examples in routes.items():
        for ex in examples:
            emb = model.encode(ex).astype(np.float32).tobytes()
            key = f"doc:{route}:{hash(ex)}"
            redis_client.hset(key, mapping={
                "route": route,
                "text": ex,
                "embedding": emb
            })
    print("✅ Stored reference embeddings")

# route a new text
def route_text(text):
    q_emb = model.encode(text).astype(np.float32).tobytes()
    from redis.commands.search.query import Query

    q = Query(f"*=>[KNN 1 @embedding $vec as score]") \
        .return_fields("route", "text", "score") \
        .sort_by("score") \
        .dialect(2)

    client = redis_client.ft("semantic_router_idx")
    res = client.search(q, query_params={"vec": q_emb})
    if res.docs:
        return res.docs[0].route
    return "No route found"

# run setup
create_index()
store_references()

# test
tests = [
    "Explain LangChain to me",
    "I want to watch Star Wars",
    "Play me some Mozart"
]

for t in tests:
    print(f"Input: {t} → Route: {route_text(t)}")
