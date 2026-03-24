import pandas as pd
from rdflib import Graph
import numpy as np
import os
import torch
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

def prepare_data(nt_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    g = Graph()
    g.parse(nt_path, format="nt")
    
    triples = []
    for s, p, o in g:
        # Simple local name extraction for readability
        s_name = s.split('#')[-1] if '#' in s else s.split('/')[-1]
        p_name = p.split('#')[-1] if '#' in p else p.split('/')[-1]
        o_name = o.split('#')[-1] if '#' in o else o.split('/')[-1]
        triples.append([s_name, p_name, o_name])
    
    df = pd.DataFrame(triples, columns=['head', 'relation', 'tail'])
    
    # Save raw triples
    df.to_csv(f"{out_dir}/triples.tsv", sep='\t', index=False, header=False)
    
    # Create TriplesFactory
    tf = TriplesFactory.from_labeled_triples(df.values)
    
    # Train/Valid/Test splits (since data is very small, 80/10/10)
    training, testing, validation = tf.split([0.8, 0.1, 0.1])
    
    # Save dataset splits for rubric compliance
    np.savetxt(f"{out_dir}/train.txt", training.mapped_triples.numpy(), fmt="%d")
    np.savetxt(f"{out_dir}/test.txt", testing.mapped_triples.numpy(), fmt="%d")
    np.savetxt(f"{out_dir}/valid.txt", validation.mapped_triples.numpy(), fmt="%d")
    
    return training, testing, validation

def train_and_eval(training, testing, validation, model_name, epochs=20):
    print(f"\n--- Training {model_name} ---")
    result = pipeline(
        training=training,
        testing=testing,
        validation=validation,
        model=model_name,
        training_kwargs=dict(num_epochs=epochs),
        evaluation_kwargs=dict(batch_size=16)
    )
    
    metrics = result.metric_results.to_df()
    print("Metrics columns:", metrics.columns.tolist())
    
    # Try different column sets based on pykeen version
    try:
        if 'Type' in metrics.columns:
            mrr = metrics[(metrics['Side'] == 'both') & (metrics['Type'] == 'realistic') & (metrics['Metric'] == 'inverse_harmonic_mean_rank')]['Value'].values[0]
            hits_at_1 = metrics[(metrics['Side'] == 'both') & (metrics['Type'] == 'realistic') & (metrics['Metric'] == 'hits_at_k') & (metrics['Step'] == 1)]['Value'].values[0]
            hits_at_3 = metrics[(metrics['Side'] == 'both') & (metrics['Type'] == 'realistic') & (metrics['Metric'] == 'hits_at_k') & (metrics['Step'] == 3)]['Value'].values[0]
            hits_at_10 = metrics[(metrics['Side'] == 'both') & (metrics['Type'] == 'realistic') & (metrics['Metric'] == 'hits_at_k') & (metrics['Step'] == 10)]['Value'].values[0]
        else:
            # Fallback for newer pykeen
            mrr = result.metric_results.get_metric('inverseharmonicmeanrank')
            hits_at_1 = result.metric_results.get_metric('hits@1')
            hits_at_3 = result.metric_results.get_metric('hits@3')
            hits_at_10 = result.metric_results.get_metric('hits@10')
    except Exception as e:
        print(f"Error extracting metrics: {e}")
        mrr, hits_at_1, hits_at_3, hits_at_10 = 0, 0, 0, 0
    
    print(f"Results for {model_name}:")
    print(f"MRR: {mrr:.4f}, Hits@1: {hits_at_1:.4f}, Hits@3: {hits_at_3:.4f}, Hits@10: {hits_at_10:.4f}")
    
    return result

def plot_tsne(result, tf, out_path):
    # Get entity embeddings
    entity_embeddings = result.model.entity_representations[0](indices=None).detach().cpu().numpy()
    
    # Run t-SNE
    tsne = TSNE(n_components=2, perplexity=min(30, len(entity_embeddings)-1), random_state=42)
    embeddings_2d = tsne.fit_transform(entity_embeddings)
    
    plt.figure(figsize=(10, 8))
    plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])
    
    # Annotate points
    for idx, (entity, e_id) in enumerate(tf.entity_to_id.items()):
        plt.annotate(entity, (embeddings_2d[e_id, 0], embeddings_2d[e_id, 1]), fontsize=8, alpha=0.7)
        
    plt.title("t-SNE of Entity Embeddings")
    plt.savefig(out_path)
    print(f"Saved t-SNE plot to {out_path}")

if __name__ == "__main__":
    nt_path = "kg_artifacts/expanded.nt"
    out_dir = "data/kge_datasets"
    
    training, testing, validation = prepare_data(nt_path, out_dir)
    
    result_transe = train_and_eval(training, testing, validation, 'TransE', epochs=50)
    result_distmult = train_and_eval(training, testing, validation, 'DistMult', epochs=50)
    
    plot_tsne(result_transe, training, "reports/tsne_transe.png")
