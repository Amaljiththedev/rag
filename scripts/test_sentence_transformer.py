from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer('all-MiniLM-L6-v2')

# Two sentences that mean roughly the same thing, worded differently
sentence_a = "Total research and development expense was $4.5 billion in 2013."
sentence_b = "How much did Apple spend on R&D?"

# A sentence about a completely different topic
sentence_c = "Tesla operates manufacturing facilities in Austin, Texas and Berlin, Germany."

vec_a = model.encode(sentence_a)
vec_b = model.encode(sentence_b)
vec_c = model.encode(sentence_c)

similarity_ab = cos_sim(vec_a, vec_b)
similarity_ac = cos_sim(vec_a, vec_c)

print(f"Similarity (R&D expense vs R&D question): {similarity_ab.item():.4f}")
print(f"Similarity (R&D expense vs Tesla factories): {similarity_ac.item():.4f}")
