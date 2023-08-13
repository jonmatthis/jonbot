from pydantic import BaseModel, Field

from jonbot.system.path_getters import get_chroma_vector_store_path


class VectorStoreMemoryConfig(BaseModel):
    collection_name: str = Field(default='vector_store')
    persistence_path: str = Field(default=get_chroma_vector_store_path())
