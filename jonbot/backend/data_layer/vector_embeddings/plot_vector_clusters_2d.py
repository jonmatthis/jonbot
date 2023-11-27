import random
from typing import List

import numpy as np
from matplotlib import cm
from plotly import graph_objects as go, io as pio
from scipy.spatial import ConvexHull
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE


def visualize_clusters_2d(embeddings: np.ndarray,
                          labels: List[str], n_clusters: int):
    unique_labels = list(np.unique(labels))
    colors = cm.rainbow(np.linspace(0, 1, len(unique_labels)))
    random.shuffle(colors)
    color_dict = dict(zip(unique_labels, colors))
    # alpha = 0.5
    # for label, color in color_dict.items():
    #     color_dict[label][-1] = alpha

    tsne = TSNE(n_components=2,
                random_state=42,
                perplexity=3)

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
        cluster_dot_xs = embeddings_2d[cluster_indices, 0].ravel()
        cluster_dot_ys = embeddings_2d[cluster_indices, 1].ravel()
        cluster_dot_labels = [labels[i] for i in cluster_indices[0]]

        if len(cluster_dot_xs) >= 3:  # Convex hull needs at least 3 points
            hull = ConvexHull(np.column_stack([cluster_dot_xs, cluster_dot_ys]))
            for simplex in hull.simplices:
                data.append(go.Scatter(x=cluster_dot_xs[simplex],
                                       y=cluster_dot_ys[simplex],
                                       mode='lines',
                                       line=dict(color=cluster_colors[cluster], width=2),
                                       hoverinfo='skip'))
        for dot_x, dot_y, dot_label in zip(cluster_dot_xs, cluster_dot_ys, cluster_dot_labels):
            data.append(go.Scatter(x=[dot_x],
                                   y=[dot_y],
                                   mode='markers',
                                   marker=dict(size=10,
                                               color=color_dict[dot_label],
                                               line=dict(width=1, color='Black')),  # outlines the marker with black
                                   text=[f'Label: {dot_label}'],  # adding labels
                                   hoverinfo='text',
                                   name=f'Channel: {dot_label}'))

    layout = go.Layout(title='t-SNE Visualization of Vectorstore Clustering with KMeans',
                       xaxis=dict(title='Dimension 1'),
                       yaxis=dict(title='Dimension 2'),
                       showlegend=True)

    fig = go.Figure(data=data, layout=layout)
    # Save the plot as an HTML file
    pio.write_html(fig, "vector_store_output.html")

    fig.show()
