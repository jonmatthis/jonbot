from typing import List, Any, Dict

import numpy as np
import pandas as pd
import plotly.express as px
from plotly import io as pio
from sklearn.manifold import TSNE


def visualize_clusters_3d(embeddings: np.ndarray,
                          text_contents: List[str],
                          metadatas=List[Dict[str, Any]]):
    tsne = TSNE(n_components=3,
                random_state=2,
                perplexity=5)
    embeddings_3d = tsne.fit_transform(embeddings)

    df = pd.DataFrame(embeddings_3d, columns=['Dimension 1', 'Dimension 2', 'Dimension 3'])
    df['text_contents'] = text_contents
    df['category_name'] = [metadata["category_name"] for metadata in metadatas]
    df['channel_name'] = [metadata["channel_name"] for metadata in metadatas]
    df['thread_name'] = [metadata["thread_name"] for metadata in metadatas]

    fig = px.scatter_3d(df,
                        x='Dimension 1',
                        y='Dimension 2',
                        z='Dimension 3',
                        color='channel_name',
                        symbol='category_name',
                        hover_name='thread_name',
                        )
    pio.write_html(fig, "vector_store_output_3d.html")

    fig.show()
