from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Company(Base):
    __tablename__ = "companies"

    osm_id: Mapped[str] = mapped_column(String, primary_key=True)
    osm_type: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pages = relationship("CompanyPage", back_populates="company", cascade="all, delete-orphan")
    vector = relationship("CompanyVector", back_populates="company", uselist=False, cascade="all, delete-orphan")


class CompanyPage(Base):
    __tablename__ = "company_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_osm_id: Mapped[str] = mapped_column(ForeignKey("companies.osm_id"), index=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="pages")


class CompanyVector(Base):
    __tablename__ = "company_vectors"

    company_osm_id: Mapped[str] = mapped_column(ForeignKey("companies.osm_id"), primary_key=True)
    model_name: Mapped[str] = mapped_column(String, default="hashing_vectorizer_v1")
    vector_dim: Mapped[int] = mapped_column(Integer)
    vector_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company", back_populates="vector")
