from sqlalchemy import (
    Column, String, Integer, Boolean, Float, Text, DateTime, ForeignKey, JSON, Enum as SAEnum,
    Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .settings import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    plate = Column(String(20), nullable=False, unique=True)
    vin = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    engine_number = Column(String(50), nullable=True)
    fuel_type = Column(String(30), nullable=True)
    mileage = Column(Integer, nullable=True)
    client_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inspections = relationship("InspectionModel", back_populates="vehicle")

    __table_args__ = (
        Index("idx_vehicle_plate", "plate"),
        Index("idx_vehicle_client", "client_id"),
    )


class InspectionModel(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    inspector_id = Column(String(36), nullable=False)
    status = Column(String(20), default="draft")
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    mileage_at_inspection = Column(Integer, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    client_id = Column(String(36), nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("VehicleModel", back_populates="inspections")
    items = relationship("InspectionItemModel", back_populates="inspection", cascade="all, delete-orphan")
    images = relationship("InspectionImageModel", back_populates="inspection", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="inspection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_inspection_vehicle", "vehicle_id"),
        Index("idx_inspection_inspector", "inspector_id"),
        Index("idx_inspection_status", "status"),
        Index("idx_inspection_client", "client_id"),
    )


class InspectionItemModel(Base):
    __tablename__ = "inspection_items"

    id = Column(String(36), primary_key=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    observation = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    is_pass = Column(Boolean, nullable=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inspection = relationship("InspectionModel", back_populates="items")
    images = relationship("InspectionImageModel", back_populates="item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_item_inspection", "inspection_id"),
        Index("idx_item_category", "category"),
    )


class InspectionImageModel(Base):
    __tablename__ = "inspection_images"

    id = Column(String(36), primary_key=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("inspection_items.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(50), default="image/jpeg")
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    caption = Column(Text, nullable=True)
    is_cover = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inspection = relationship("InspectionModel", back_populates="images")
    item = relationship("InspectionItemModel", back_populates="images")

    __table_args__ = (
        Index("idx_image_inspection", "inspection_id"),
        Index("idx_image_item", "item_id"),
    )


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False)
    template_id = Column(String(36), nullable=False)
    doc_type = Column(String(10), default="pdf")
    status = Column(String(20), default="pending")
    title = Column(String(200), default="")
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    generation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inspection = relationship("InspectionModel", back_populates="documents")

    __table_args__ = (
        Index("idx_document_inspection", "inspection_id"),
    )


class TemplateModel(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="general")
    content = Column(Text, default="")
    variables = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_template_category", "category"),
    )


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(200), nullable=False)
    role = Column(String(20), default="inspector")
    is_active = Column(Boolean, default=True)
    phone = Column(String(30), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
    )
