from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Dict, List
from thefuzz import fuzz

Base = declarative_base()

class SongAlias:
    def __init__(self, database_path: str):
        self.engine = create_engine(f'sqlite:///{database_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    class SongAliasModel(Base):
        __tablename__ = "song_alias"
        
        alias = Column(String, primary_key=True)
        id = Column(String)
    
    def get_song_id(self, song_alias: str, fit: int = 80) -> Dict[str, str]:
        session = self.Session()
        try:
            records = session.query(self.SongAliasModel).all()
            res = {}
            
            if records:
                match = []
                for record in records:
                    match.append((record.alias, fuzz.token_set_ratio(song_alias, record.alias)))
                
                for alias, score in match:
                    if score >= fit:
                        result = session.query(self.SongAliasModel).filter(self.SongAliasModel.alias == alias).first()
                        if result is None:
                            continue
                        if alias.lower() == song_alias.lower():
                            return {alias: result.id}
                        res[alias] = result.id
                
                if len(res) > 1:
                    for alias in res:
                        if alias.lower() == song_alias.lower():
                            return {alias: res[alias]}
            
            return res
        finally:
            session.close()
    
    def get_song_alias(self, songID: str) -> List[str]:
        session = self.Session()
        try:
            results = session.query(self.SongAliasModel.alias).filter(self.SongAliasModel.id == songID).all()
            return [result[0] for result in results] if results else []
        finally:
            session.close()
    
    def add_song_alias(self, songAlias: str, songID: str) -> None:
        session = self.Session()
        try:
            existing = session.query(self.SongAliasModel).filter(self.SongAliasModel.alias == songAlias).first()
            if existing:
                print(f"Error: The alias '{songAlias}' already exists.")
                return
            
            new_alias = self.SongAliasModel(alias=songAlias, id=songID)
            session.add(new_alias)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding alias '{songAlias}': {e}")
        finally:
            session.close()
    
    def remove_song_alias(self, songAlias: str) -> None:
        session = self.Session()
        try:
            session.query(self.SongAliasModel).filter(self.SongAliasModel.alias == songAlias).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error deleting alias '{songAlias}': {e}")
        finally:
            session.close()

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
song_alias = SongAlias(os.path.join(current_dir, "song_alias.db"))
