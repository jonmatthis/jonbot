import asyncio

import dash
import numpy as np
import pandas as pd
import plotly.express as px
from dash import html, dcc
from dash.dependencies import Input, Output, State
from sklearn.manifold import TSNE

from jonbot.backend.data_layer.vector_embeddings.create_vector_store import get_or_create_vectorstore


async def fetch_data(vector_store):
    collection = vector_store._collection.get(include=["embeddings", "documents", "metadatas"])
    return np.array(collection["embeddings"]), collection["documents"], collection["metadatas"]


app = dash.Dash(__name__)


def create_layout():
    return html.Div([
        dcc.Graph(id='scatter3d-plot', style={'display': 'inline-block', 'width': '70%', 'height': '100vh'}),

        html.Div([
            html.Div([
                html.Label('Perplexity:'),
                dcc.Slider(
                    id='perplexity-slider',
                    min=5, max=50, value=30,
                    step=1,
                    marks={i: str(i) for i in range(5, 55, 5)}
                )
            ], style={'marginBottom': 20})
        ], style={
            'display': 'inline-block',
            'width': '30%',
            'verticalAlign': 'middle',
            'marginLeft': 20
        })

    ], style={'textAlign': 'center', 'marginTop': 50})


app.layout = create_layout()

@app.callback(
    [Output('modal', 'is_open'),
     Output('modal-body', 'children')],
    [Input('scatter3d-plot', 'clickData')],
    [State('modal', 'is_open')]
)
def display_click_data(clickData, is_open):
    if clickData is not None:
        point_index = clickData['points'][0]['pointIndex']
        text = text_contents[point_index]
        return not is_open, text
    return is_open, None

@app.callback(
    Output('scatter3d-plot', 'figure'),
    [Input('perplexity-slider', 'value')]
)
def update_figure(perplexity, random_state=42):
    global embeddings, text_contents, metadatas
    tsne = TSNE(n_components=3, random_state=random_state, perplexity=perplexity)
    embeddings_3d = tsne.fit_transform(embeddings)
    df = pd.DataFrame(embeddings_3d, columns=['Dimension 1', 'Dimension 2', 'Dimension 3'])
    df['text_contents'] = text_contents
    df['category_name'] = [metadata["category_name"] for metadata in metadatas]
    df['channel_name'] = [metadata["channel_name"] for metadata in metadatas]
    df['thread_name'] = [metadata["thread_name"] for metadata in metadatas]
    fig = px.scatter_3d(df, x='Dimension 1', y='Dimension 2', z='Dimension 3',
                        color='channel_name', symbol='category_name', hover_name='thread_name')
    return fig


if __name__ == '__main__':
    database_name = "classbot_database"
    server_id = 1150736235430686720
    chroma_collection_name = "classbot_vector_store"
    chroma_persistence_directory = "classbot_chroma_persistence"

    vector_store = asyncio.run(get_or_create_vectorstore(
        chroma_collection_name=chroma_collection_name,
        chroma_persistence_directory=chroma_persistence_directory,
        server_id=server_id,
        database_name=database_name
    ))
    embeddings, text_contents, metadatas = asyncio.run(fetch_data(vector_store))
    app.run_server(debug=True)
