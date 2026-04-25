from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class NaicsSector(Base):
    __tablename__ = "naics_sectors"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    naics_version: Mapped[str] = mapped_column(String, default="2022")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CompanyIndustryLabel(Base):
    __tablename__ = "company_industry_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_osm_id: Mapped[str] = mapped_column(ForeignKey("companies.osm_id"), index=True)
    label_source: Mapped[str] = mapped_column(String, default="gpt")
    naics_sector_code: Mapped[str] = mapped_column(ForeignKey("naics_sectors.code"), index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    alternate_sector_code: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company = relationship("Company")
    sector = relationship("NaicsSector")


class IndustryModelRun(Base):
    __tablename__ = "industry_model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_type: Mapped[str] = mapped_column(String, default="industry_nb")
    model_name: Mapped[str] = mapped_column(String)
    artifact_path: Mapped[str] = mapped_column(String)
    label_space_version: Mapped[str] = mapped_column(String, default="naics_2022_2digit")
    train_count: Mapped[int] = mapped_column(Integer, default=0)
    val_count: Mapped[int] = mapped_column(Integer, default=0)
    test_count: Mapped[int] = mapped_column(Integer, default=0)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompanyIndustryPrediction(Base):
    __tablename__ = "company_industry_predictions"

    company_osm_id: Mapped[str] = mapped_column(ForeignKey("companies.osm_id"), primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("industry_model_runs.id"), primary_key=True)
    predicted_sector_code: Mapped[str] = mapped_column(ForeignKey("naics_sectors.code"), index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    probabilities_json: Mapped[str] = mapped_column(Text)
    predicted_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    model_run = relationship("IndustryModelRun")
    sector = relationship("NaicsSector")
