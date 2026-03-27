from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import Base
import uuid
import enum

class AdPlatform(str, enum.Enum):
    meta_ads = "meta_ads"
    google_ads = "google_ads"

class AdStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    PENDING = "PENDING"
    ERROR = "ERROR"

class AdAccount(Base):
    __tablename__ = "ad_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    platform = Column(SQLEnum(AdPlatform), nullable=False)
    account_id = Column(String(255), nullable=False) # ID in Meta/Google
    name = Column(String(255), nullable=True) # Nome do BM/Conta
    access_token = Column(String(1000), nullable=True) # Token OAuth
    status = Column(SQLEnum(AdStatus), default=AdStatus.PENDING)
    last_sync_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", backref="ad_accounts")
    campaigns = relationship("AdCampaign", back_populates="account", cascade="all, delete-orphan")

class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    ad_account_id = Column(String(36), ForeignKey("ad_accounts.id"), nullable=False)
    
    platform_campaign_id = Column(String(255), nullable=False) # ID numérico nativo
    name = Column(String(255), nullable=False)
    budget_daily = Column(Float, default=0.0)
    status = Column(SQLEnum(AdStatus), default=AdStatus.ACTIVE)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("AdAccount", back_populates="campaigns")
    metrics = relationship("AdMetric", back_populates="campaign", cascade="all, delete-orphan")

class AdMetric(Base):
    __tablename__ = "ad_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    ad_campaign_id = Column(String(36), ForeignKey("ad_campaigns.id"), nullable=False)
    
    date = Column(Date, nullable=False, index=True) # Agrupado por Dia
    spend = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    leads_platform = Column(Integer, default=0) # Contados pelo Meta Pixel
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campaign = relationship("AdCampaign", back_populates="metrics")
