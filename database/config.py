import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

class DatabaseConfig:
    """Database configuration and session management"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = create_engine(
            self.database_url,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _get_database_url(self):
        """Get database URL from environment variables"""
        db_host = os.getenv("DB_HOST", "localhost")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "mysecretpassword")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "ice")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def create_all_tables(self):
        """Create all tables (for development use)"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all_tables(self):
        """Drop all tables (for development use)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()

# Global database instance
db_config = DatabaseConfig()