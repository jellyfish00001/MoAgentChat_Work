"""Central settings loaded from server/.env (or repo-root .env)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# settings.py -> config -> flows -> server
SERVER_ROOT = Path(__file__).resolve().parents[2]
# server -> ai_prepare repo root
REPO_ROOT = SERVER_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            SERVER_ROOT / ".env",
            REPO_ROOT / ".env",
            Path.cwd() / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    langchain_tracing_v2: bool = Field(default=True, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langchain_project: str = Field(default="ai_prepare", alias="LANGCHAIN_PROJECT")

    az_tenant_id: str = Field(default="", alias="AZ_TENANT_ID")
    az_client_id: str = Field(default="", alias="AZ_CLIENT_ID")
    az_client_secret: str = Field(default="", alias="AZ_CLIENT_SECRET")
    az_scope: str = Field(
        default="https://cognitiveservices.azure.com/.default",
        alias="AZ_SCOPE",
    )
    az_llm_endpoint: str = Field(default="", alias="AZ_LLM_ENDPOINT")
    az_llm_version: str = Field(default="2025-03-01-preview", alias="AZ_LLM_VERSION")
    llm_model_name: str = Field(default="", alias="LLM_MODEL_NAME")
    ocp_apim_subscription_key: str = Field(default="", alias="OCP_APIM_SUBSCRIPTION_KEY")

    flows_testdata_root: str = Field(default="", alias="FLOWS_TESTDATA_ROOT")
    rework_mo_data: str = Field(default="", alias="REWORK_MO_DATA")
    rd_risk_data: str = Field(default="", alias="RD_RISK_DATA")
    qv_dms_data: str = Field(default="", alias="QV_DMS_DATA")

    # MVP caps to avoid huge LLM / scan runs
    flows_analysis_limit: int = Field(default=5, alias="FLOWS_ANALYSIS_LIMIT")
    flows_rd_sample_limit: int = Field(default=50, alias="FLOWS_RD_SAMPLE_LIMIT")

    # 寄信（選填）：MAIL_BACKEND 空白＝不開寄信；URL 含 sig 等於密碼，只放 .env／Vault
    mail_backend: str = Field(default="", alias="MAIL_BACKEND")
    mail_allowed_domains: str = Field(default="", alias="MAIL_ALLOWED_DOMAINS")
    mail_logic_app_url: str = Field(default="", alias="MAIL_LOGIC_APP_URL")

    def _testdata_root(self) -> Path:
        if self.flows_testdata_root:
            return Path(self.flows_testdata_root)
        return SERVER_ROOT / "testdata"

    def rework_mo_data_dir(self) -> Path:
        if self.rework_mo_data:
            return Path(self.rework_mo_data)
        return self._testdata_root() / "rework_mo"

    def rd_risk_data_dir(self) -> Path:
        if self.rd_risk_data:
            return Path(self.rd_risk_data)
        return self._testdata_root() / "rd_risk"

    def qv_dms_data_dir(self) -> Path:
        if self.qv_dms_data:
            return Path(self.qv_dms_data)
        return self._testdata_root() / "qv_dms"

    def outputs_dir(self) -> Path:
        return SERVER_ROOT / "outputs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
