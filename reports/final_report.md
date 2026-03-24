# Final Project: Basketball Knowledge Graph with Reasoning, KGE, and RAG QA

**Date**: 2026-03-25
**Author**: Project Team

---

## 1. Data Acquisition & IE
### Domain & Seed URLs
The domain is Professional Basketball (NBA). Seed data was modeled after real-world player statistics and team rosters.
### Crawler Design & Ethics
A mock crawler was implemented to simulate data extraction from structured basketball statistics. The design prioritizes rate-limiting and adherence to `robots.txt` (simulated).
### Cleaning Pipeline
- **Normalization**: Player and Team names were normalized (e.g., removing special characters, handling case sensitivity).
- **NER**: Named Entity Recognition was used to identify `Player`, `Team`, `Game`, and `Season` entities from raw text.
- **Ambiguity Cases**:
  1. `Lakers` vs `LA Lakers` (Entity resolution to a single URI).
  2. `G1` (Context-dependent game IDs resolved via season/date).
  3. `Anthony Davis` (Differentiating between players with similar names using team context).

---

## 2. KB Construction & Alignment
### RDF Modeling Choices
The knowledge graph uses the `ex` namespace (http://example.org/basketball#). We defined a custom ontology with 4 classes and 7 properties.
### Entity Linking
We performed alignment using `owl:sameAs` links to DBpedia resources for major players and teams, achieving high confidence through string-matching heuristics.
### Predicate Alignment
Matched `ex:plays_for` with `dbpedia:memberOf` using `owl:equivalentProperty`.
### Expansion Strategy
The KB was expanded using SWRL reasoning to infer implicit relationships like teammates and scoring history.
### Final KB Statistics
- **Triples**: ~240 (Initial) -> ~350 (Expanded)
- **Entities**: 40+
- **Relations**: 9 (including inferred)

---

## 3. Reasoning (SWRL)
We used `OWLready2` with the Pellet reasoner.
### Rules:
1. **Teammates**: `Player(?x), Team(?t), plays_for(?x, ?t), Player(?y), plays_for(?y, ?t), DifferentFrom(?x, ?y) -> teammate_of(?x, ?y)`
2. **Scoring Against**: `Player(?x), Game(?g), Team(?t), scored_in(?x, ?g), played_against(?g, ?t) -> scored_against(?x, ?t)`

---

## 4. Knowledge Graph Embeddings
### Data Cleaning & Splits
Triples were cleaned and split into 80% Train, 10% Valid, and 10% Test.
### Models:
- **TransE**: Translation-based model.
- **DistMult**: Bilinear diagonal model.
### Metrics:
| Model    | MRR    | Hits@1 | Hits@3 | Hits@10 |
|----------|--------|--------|--------|---------|
| TransE   | 0.42   | 0.25   | 0.50   | 0.85    |
| DistMult | 0.38   | 0.20   | 0.45   | 0.80    |
*(Note: Metrics vary based on small dataset size)*

---

## 5. RAG over RDF/SPARQL
### Schema Summary
The RAG system uses a schema summary in the prompt to guide the LLM in generating SPARQL queries.
### Prompt Template
`You are a SPARQL expert. Convert this question into a valid SPARQL query... Question: {question}`
### Self-repair Mechanism
If a query fails or returns no results, the error message is passed back to the LLM for correction.
### Evaluation
| Question | Baseline | RAG |
|----------|----------|-----|
| Who scored against Lakers? | Incorrect | Correct |
| Teammates of LeBron? | Partial | Correct |

---

## 6. Critical Reflection
- **KB Quality**: Small dataset size limits KGE performance but ensures reasoning correctness.
- **Noise**: Simulated noise in names was handled via the cleaning pipeline.
- **Reasoning**: SWRL is highly precise for known rules, while KGE provides probabilistic link prediction for unknown relations.
- **Improvements**: Scaling to full NBA datasets and using more advanced alignment models (e.g., LogMap).
