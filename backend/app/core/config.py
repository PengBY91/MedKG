from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Governance Tool"
    API_V1_STR: str = "/api/v1"
    
    # Mock Database Config
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "medkg2024"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: str = "19530"

    class Config:
        case_sensitive = True

settings = Settings()
