from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, JSON, Float, DateTime
from datetime import datetime
from pydantic import BaseModel, Field

class Player(BaseModel):
    object_id: str
    
    rating: float
    
    exp: int = 0
    level: float = 1
    
    all_perfect_plus: int = 0
    all_perfect: int = 0
    full_combo: int = 0
    
    miss: int = 0
    good: int = 0
    perfect: int = 0
    perfect_plus: int = 0
    
    play_record: dict = Field(default_factory=dict)

class PlayerData:
    _base = declarative_base()
    
    class PlayerLatest(_base):
        __tablename__ = "player_latest"
        
        object_id = Column(String, primary_key=True)
        
        rating = Column(Float, nullable=False)
        
        exp = Column(Integer, nullable=True)
        level = Column(Float, nullable=True)
        
        all_perfect_plus = Column(Integer, nullable=True)
        all_perfect = Column(Integer, nullable=True)
        full_combo = Column(Integer, nullable=True)
        
        miss = Column(Integer, nullable=True)
        good = Column(Integer, nullable=True)
        perfect = Column(Integer, nullable=True)
        perfect_plus = Column(Integer, nullable=True)

        play_record = Column(JSON, nullable=True)
    
    class PlayerHistory(_base):
        __tablename__ = "player_history"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        timestamp = Column(DateTime, nullable=False, index=True, default=lambda: datetime.now())
        
        object_id = Column(String, nullable=False)
        
        rating = Column(Float, nullable=False)
        
        exp = Column(Integer, nullable=True)
        level = Column(Float, nullable=True)
        
        all_perfect_plus = Column(Integer, nullable=True)
        all_perfect = Column(Integer, nullable=True)
        full_combo = Column(Integer, nullable=True)
        
        miss = Column(Integer, nullable=True)
        good = Column(Integer, nullable=True)
        perfect = Column(Integer, nullable=True)
        perfect_plus = Column(Integer, nullable=True)

        play_record = Column(JSON, nullable=True)
    
    def __init__(self, database_path: str) -> None:
        self.engine = create_engine(f'sqlite:///{database_path}')
        self._base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)
    
    def add_player(self, player: Player, timestamp: datetime = None) -> None:
        session = self.session()
        try:
            player_latest = self.PlayerLatest(**player.model_dump())
            session.merge(player_latest)
            
            if timestamp is None:
                timestamp = datetime.now()
            player_history = self.PlayerHistory(
                timestamp=timestamp,
                **player.model_dump()
            )
            session.add(player_history)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Player data commit or ??? has a mistake: {e}")
            raise
        finally:
            session.close()
    
    def get_player_latest(self, object_id: str, is_dict: bool = False) -> Player | dict | None:
        session = self.session()
        try:
            player = session.query(self.PlayerLatest).filter_by(object_id=object_id).first()
            if player is None: return None
            if is_dict:
                return {c.key: getattr(player, c.key) for c in player.__table__.columns}
            return Player(**{c.key: getattr(player, c.key) for c in player.__table__.columns})
        finally:
            session.close()
    
    def get_player_history(self, object_id: str, since: datetime = None, limit: int = 100, order_desc: bool = True) -> list[dict]:
        session = self.session()
        try:
            query = session.query(self.PlayerHistory).filter_by(object_id=object_id)
            if since:
                query = query.filter(self.PlayerHistory.timestamp >= since)
            if order_desc:
                query = query.order_by(self.PlayerHistory.timestamp.desc())
            else:
                query = query.order_by(self.PlayerHistory.timestamp.asc())
            rows = query.limit(limit).all()
            return [
                {c.key: getattr(row, c.key) for c in row.__table__.columns}
                for row in rows
            ]
        finally:
            session.close()

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
player_data = PlayerData(os.path.join(current_dir, "player_data.db"))
