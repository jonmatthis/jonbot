from pydantic import BaseModel, Field

from jonbot.layer3_data_layer.system.filenames_and_paths import get_chroma_vector_store_path


class VectorStoreMemoryConfig(BaseModel):
    collection_name: str = Field(default='vector_store')
    persistence_path: str = Field(default=get_chroma_vector_store_path())

