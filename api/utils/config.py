import os

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "../storage/store.db")
    POS_DATA_PATH = os.getenv("POS_DATA_PATH", "../data/pos/brigade_pos.csv")
