import asyncio
from typing import List, Any, Dict

import numpy as np
import pandas as pd
import plotly.express as px
from plotly import io as pio
from pygments.lexers import go
from sklearn.manifold import TSNE


def visualize_clusters_3d(embeddings: np.ndarray,
                          text_contents: List[str],
                          metadatas=List[Dict[str, Any]]):
    tsne = TSNE(n_components=3,
                random_state=2,
                perplexity=5)
    embeddings_3d = tsne.fit_transform(embeddings)

    # # get all chat id
    # chat_ids = [metadata["chat_id"] for metadata in metadatas]
    # # get unique chat ids
    # unique_chat_ids = list(set(chat_ids))
    # couplets_by_chatid = {}
    # for chat_id in unique_chat_ids:
    #     #get all the entries that have the same chat id
    #     for metadata in metadatas:
    #         if metadata["chat_id"] == chat_id:
    #             if not chat_id in couplets_by_chatid:
    #                 couplets_by_chatid[chat_id] = []
    #             couplets_by_chatid[chat_id].append(metadata["couplet"])
    #
    # # go through each entry in couplets_by_chatid and re-order the entries according to `metadatas['couplet_number']`
    # for chat_id, couplets in couplets_by_chatid.items():
    #     couplets_by_chatid[chat_id] = sorted(couplets, key=lambda x: x["couplet_number"])
    #


    df = pd.DataFrame(embeddings_3d, columns=['Dimension 1', 'Dimension 2', 'Dimension 3'])
    df['text_contents'] = text_contents
    df['category_name'] = [metadata["category_name"] for metadata in metadatas]
    df['channel_name'] = [metadata["channel_name"] for metadata in metadatas]
    df['thread_name'] = [metadata["thread_name"] for metadata in metadatas]

    # fig = px.scatter_3d(df,
    #                     x='Dimension 1',
    #                     y='Dimension 2',
    #                     z='Dimension 3',
    #                     color='channel_name',
    #                     symbol='category_name',
    #                     hover_name='thread_name',
    #                     )
    # pio.write_html(fig, "vector_store_output_3d.html")
    #
    # fig.show()


    # Create a 3D scatter plot using plotly.graph_objects
    fig = go.Figure()

    # Loop through each chat id and plot the lines
    for chat_id, couplets in couplets_by_chatid.items():
        # Get indices for couplets in the current chat
        indices = [metadatas.index(couplet) for couplet in couplets]
        # Extract the corresponding embeddings
        chat_embeddings = embeddings_3d[indices, :]

        # Create a line for each couplet
        fig.add_trace(go.Scatter3d(
            x=chat_embeddings[:, 0],
            y=chat_embeddings[:, 1],
            z=chat_embeddings[:, 2],
            mode='lines+markers',
            name=f'Chat {chat_id}'
        ))

    # Setting the title and axes titles
    fig.update_layout(title="3D visualization of Text Embeddings",
                      scene=dict(xaxis_title='Dimension 1',
                                 yaxis_title='Dimension 2',
                                 zaxis_title='Dimension 3'))

    # Saving and showing the figure
    pio.write_html(fig, "vector_store_output_3d.html")
    fig.show()