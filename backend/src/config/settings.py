import os
DATABASE_URL=os.environ.get("DATABASE_URL","postgresql+psycopg://journey:journey@db/journey")
REDIS_URL=os.environ.get("REDIS_URL","redis://redis:6379/0")
JWT_SECRET=os.environ.get("JWT_SECRET","local-journey-credit-change-this-key")
SEED_DEMO=os.environ.get("SEED_DEMO","true").lower()=="true"
ATTRIBUTION_MAX_CHANNELS=int(os.environ.get("ATTRIBUTION_MAX_CHANNELS","2000"))
ATTRIBUTION_MAX_EDGES=int(os.environ.get("ATTRIBUTION_MAX_EDGES","20000"))
ATTRIBUTION_TIME_LIMIT_S=int(os.environ.get("ATTRIBUTION_TIME_LIMIT_S","120"))
ATTRIBUTION_MEMORY_LIMIT_MIB=int(os.environ.get("ATTRIBUTION_MEMORY_LIMIT_MIB","512"))
