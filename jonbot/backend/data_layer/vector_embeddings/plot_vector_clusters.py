from typing import List, Any, Dict

import numpy as np
import pandas as pd
import plotly.express as px
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

    sizes = []
    try:
        for metadata in metadatas:
            if metadata['type'] == 'couplet':
                sizes.append(1)
            elif metadata['type'] == 'chat':
                sizes.append(2)
            elif metadata['type'] == 'channel':
                sizes.append(4)
            else:
                sizes.append(8)
        df['sizes'] = sizes
    except Exception as e:
        print(e)
    fig = px.scatter_3d(df,
                        x='Dimension 1',
                        y='Dimension 2',
                        z='Dimension 3',
                        color='channel_name',
                        symbol='category_name',
                        size='sizes',
                        # hover_data=['text_contents']
                        )
    fig.show()
