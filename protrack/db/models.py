from sqlalchemy.types import *
from sqlalchemy import Column, ForeignKey, and_
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, backref

from protrack.db import protrack_engine

#sqlalchemy boilerplate
Base = declarative_base()
Base.metadata.bind = protrack_engine

class Series(Base):
    """
    Protrack Series Table (from quad_tab)
    """
    __tablename__ = 'quad_tab'
    __table_args__ = ({'autoload': False})
    
    id = Column('ser_serial', Integer, primary_key = True)
    title = Column('ser_title', CHAR(length = 50, convert_unicode = True))
    nola = Column('ser_nola_base', CHAR(length = 6, convert_unicode = True))
    
class Description(Base):
    """
    Protrack Description table
    
    create table "root".progdesc 
    (
        pde_ser_id integer,
        pde_sea_id integer,
        pde_prog_id integer,
        pde_vsn_id integer,
        pde_disp_ord smallint,
        pde_text char(70),
        up_by integer,
        up_type char(1),
        up_date datetime year to second
    );
    """
    __tablename__ = "progdesc"
    __table_args__ = ({'autoload': False})
    
    season_id = Column('pde_sea_id', Integer, primary_key = True)
    series_id = Column('pde_ser_id', Integer, ForeignKey(Series.id), primary_key = True)
    episode_id = Column('pde_prog_id', Integer, primary_key = True)
    version_id = Column('pde_vsn_id', Integer, primary_key = True)
    
    desc = Column('pde_text', CHAR(length = 70, convert_unicode = True))
    display_order = Column('pde_disp_ord', SMALLINT)
    
    
    series = relationship(Series, primaryjoin = Series.id == series_id)
    
class Episode(Base):
    """
    Protrack Program Table (from quad_tab)
    
    these are episodes
    """
    __tablename__ = 'quad_tab'
    __table_args__ = ({'autoload': False, 'extend_existing': True})
    
    id = Column('pg_serial', Integer, primary_key = True)
    title = Column('pg_title', CHAR(length = 50, convert_unicode = True))
    total = Column('vsn_total', SMALLINT) 
    number = Column('vsn_order', SMALLINT)
    nola = Column('vsn_nola_code', CHAR(length = 15))
    
    @property
    def hd(self):
        mod = None
        needle = self.nola[6:]
        
        if len(needle) > 6:
            mod = needle[6:]
            
        if mod == 'H' or mod == 'Z':
            return True
        
        return False
    
    @property
    def season_number(self):
        needle = self.nola[6:]
        
        if len(needle) > 6:
            needle = needle[0:6]
        
        if self.number >= 100:
            return needle[0:(len(needle)-3)]
        else:
            return needle[0:(len(needle)-2)]
            
class ProgramGuide(Base):
    """
    create table "root".proguide 
    (
        pgu_serial serial not null ,
        pgu_ser_id integer,
        pgu_sea_id integer,
        pgu_prog_id integer,
        pgu_vsn_id integer,
        pgu_location char(15),
        pgu_text char(1024),
        up_by integer,
        up_type char(1),
        up_date datetime year to second
    );
    """
    __tablename__ = "proguide"
    __table_args__ = ({'autoload': False})
    
    id = Column('pgu_serial', Integer, primary_key = True)
    desc = Column('pgu_text', CHAR(length = 1024, convert_unicode = True))
    season_id = Column('pgu_sea_id', Integer)
    series_id = Column('pgu_ser_id', Integer)
    episode_id = Column('pgu_prog_id', Integer)
    version_id = Column('pgu_vsn_id', Integer)
    
    #series = relationship(Series, primaryjoin = Series.id == series_id, foreign_keys = [Series.id])
    #episode = relationship(Episode, primaryjoin = Episode.id == episode_id, foreign_keys = [Episode.id])


class Air(Base):
    __tablename__ = "air"
    __table_args__ = ({'autoload': False})
    
    id = Column('ai_serial', Integer, primary_key = True)
    series_id = Column('ai_ser_id', Integer)
    season_id = Column('ai_sea_id', Integer)
    episode_id = Column('ai_prog_id', Integer)
    version_id = Column('ai_vsn_id', Integer)
    on_date = Column('ai_air_date', DATE)
    at_time = Column('ai_air_time', CHAR(length = 11))
    for_length = Column('ai_air_len', CHAR(length = 11))
    
    guide = relationship(ProgramGuide, primaryjoin = and_(
                series_id == ProgramGuide.series_id,
                season_id == ProgramGuide.season_id,
                episode_id == ProgramGuide.episode_id,
                version_id == ProgramGuide.version_id,
            ),foreign_keys=[
                ProgramGuide.series_id,
                ProgramGuide.season_id,
                ProgramGuide.episode_id,
                ProgramGuide.version_id
            ])
            
class Air13(Base):
    __tablename__ = "air13"
    __table_args__ = ({'autoload': False})
    
    id = Column('ai_serial', Integer, primary_key = True)
    series_id = Column('ai_ser_id', Integer)
    season_id = Column('ai_sea_id', Integer)
    episode_id = Column('ai_prog_id', Integer)
    version_id = Column('ai_vsn_id', Integer)
    on_date = Column('ai_air_date', DATE)
    at_time = Column('ai_air_time', CHAR(length = 11))
    for_length = Column('ai_air_len', CHAR(length = 11))
    
    guide = relationship(ProgramGuide, primaryjoin = and_(
                series_id == ProgramGuide.series_id,
                season_id == ProgramGuide.season_id,
                episode_id == ProgramGuide.episode_id,
                version_id == ProgramGuide.version_id,
            ),foreign_keys=[
                ProgramGuide.series_id,
                ProgramGuide.season_id,
                ProgramGuide.episode_id,
                ProgramGuide.version_id
            ])
"""
guide = relationship("ProgramGuide", primaryjoin = and_(
                "ProgramGuide.series_id == Air.series_id",
                "ProgramGuide.season_id == Air.season_id",
                "ProgramGuide.episode_id == Air.episode_id",
                "ProgramGuide.version_id == Air.version_id",
            ),foreign_keys=[
                ProgramGuide.series_id,
                ProgramGuide.season_id,
                ProgramGuide.episode_id,
                ProgramGuide.version_id
            ])


class SafeAir(AirMixin, Base):
    __tablename__ = "safeair"
    __table_args__ = ({'autoload': False})
      
class Air13(AirMixin, Base):

class SafeAir13(AirMixin, Base)
"""