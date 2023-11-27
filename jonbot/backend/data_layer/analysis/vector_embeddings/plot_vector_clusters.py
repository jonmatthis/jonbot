from typing import Union, List

import numpy as np
from plotly import graph_objects as go
from scipy.spatial import ConvexHull
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE


def visualize_clusters(embeddings: Union[List[List[float]], np.ndarray],
                       labels: List[str], n_clusters: int):
    tsne = TSNE(n_components=2,
                random_state=42,
                perplexity=3)

    if embeddings.__class__ == list:
        embeddings = np.array(embeddings)

    embeddings_2d = tsne.fit_transform(embeddings)

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans_labels = kmeans.fit_predict(embeddings_2d)

    data = []
    cluster_colors = ['#1f77b4',
                      '#ff7f0e',
                      '#2ca02c',
                      '#d62728',
                      '#9467bd',
                      '#8c564b',
                      '#e377c2',
                      '#7f7f7f',
                      '#bcbd22',
                      '#17becf',
                      '#aec7e8',
                      '#ffbb78',
                      '#98df8a',
                      '#ff9896',
                      '#c5b0d5',
                      '#c49c94',
                      '#f7b6d2',
                      '#dbdb8d',
                      '#9edae5',
                      '#393b79',
                      '#637939',
                      '#8c6d31',
                      '#843c39',
                      '#d6616b',
                      '#7b4173',
                      '#ce6dbd',
                      '#de9ed6',
                      '#3182bd', ]

    for cluster in range(n_clusters):
        cluster_indices = np.where(kmeans_labels == cluster)
        x = embeddings_2d[cluster_indices, 0].ravel()
        y = embeddings_2d[cluster_indices, 1].ravel()

        if len(x) >= 3:  # Convex hull needs at least 3 points
            hull = ConvexHull(np.column_stack([x, y]))
            for simplex in hull.simplices:
                data.append(go.Scatter(x=x[simplex],
                                       y=y[simplex],
                                       mode='lines',
                                       line=dict(color=cluster_colors[cluster], width=2),
                                       hoverinfo='skip'))
        data.append(go.Scatter(x=x,
                               y=y,
                               mode='markers',
                               marker=dict(size=10,
                                           color=cluster_colors[cluster],
                                           line=dict(width=2, color='Black')),  # outlines the marker with black
                               text=[f'Label: {labels[i]}' for i in cluster_indices[0]],  # adding labels
                               hoverinfo='text',
                               name=f'Cluster {cluster}'))

    layout = go.Layout(title='t-SNE Visualization of Vectorstore Clustering with KMeans',
                       xaxis=dict(title='Dimension 1'),
                       yaxis=dict(title='Dimension 2'),
                       showlegend=True)

    fig = go.Figure(data=data, layout=layout)
    fig.show()
