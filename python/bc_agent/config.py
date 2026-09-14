from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT / "fixtures"


@dataclass(frozen=True)
class Settings:
    # mock = fixtures, live hoac api = goi BC that. Nhan ca hai ten vi brief va .env tung ghi
    # `BC_MODE=api`, con code chi so voi "live", nen tro ly am tham chay tren fixtures ma man hinh
    # van bao dang chay that. Bat duoc ngay 12/09/2026.
    bc_mode: str = os.getenv("BC_MODE", "mock")
    # api  = custom API page cua extension NWV Marou Data API (mac dinh)
    # odata = web service OData V4 khai tay, duong du phong khi extension chua publish
    bc_source: str = os.getenv("BC_SOURCE", "api")
    llm_mode: str = os.getenv("LLM_MODE", "scripted")
    # azure = Azure OpenAI (mac dinh tu 12/09/2026), anthropic = Claude. Chi co tac dung khi LLM_MODE=live.
    llm_provider: str = os.getenv("LLM_PROVIDER", "azure")

    # Azure OpenAI. Ten deployment la ten tu dat luc deploy, khong phai ten model.
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "").strip()

    # Claude, chi dung khi LLM_PROVIDER=anthropic.
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    agent_model: str = os.getenv("AGENT_MODEL", "claude-opus-4-8")
    # Model nhanh cho viec ngan (phan loai tin, doc cau giai thich). Azure chi co mot deployment
    # nen dung chung; Claude thi dung Haiku.
    agent_model_fast: str = os.getenv("AGENT_MODEL_FAST", "claude-haiku-4-5")

    bc_tenant_id: str = os.getenv("BC_TENANT_ID", "")
    bc_client_id: str = os.getenv("BC_CLIENT_ID", "")
    bc_client_secret: str = os.getenv("BC_CLIENT_SECRET", "")
    bc_environment: str = os.getenv("BC_ENVIRONMENT", "")
    bc_company_name: str = os.getenv("BC_COMPANY_NAME", "")
    bc_company_id: str = os.getenv("BC_COMPANY_ID", "")

    max_proposals_per_run: int = int(os.getenv("AGENT_MAX_PROPOSALS_PER_RUN", "10"))
    max_tool_iterations: int = int(os.getenv("AGENT_MAX_TOOL_ITERATIONS", "20"))
    log_dir: Path = Path(os.getenv("AGENT_LOG_DIR", "./runs"))

    @property
    def bc_live(self) -> bool:
        """Co goi BC that khong. Gia tri la nao khac ba ten da biet thi bao ngay, khong doan."""
        m = (self.bc_mode or "").strip().lower()
        if m in ("live", "api"):
            return True
        if m in ("mock", ""):
            return False
        raise SystemExit(f"BC_MODE={self.bc_mode!r} khong hop le, chi nhan mock, live hoac api")

    def validate_live_bc(self) -> None:
        missing = [
            k
            for k in ("bc_tenant_id", "bc_client_id", "bc_client_secret", "bc_environment")
            if not getattr(self, k)
        ]
        if missing:
            raise SystemExit(f"BC_MODE=live nhung thieu bien: {', '.join(m.upper() for m in missing)}")
        if not (self.bc_company_name or self.bc_company_id):
            raise SystemExit("Can BC_COMPANY_NAME hoac BC_COMPANY_ID")

    def validate_live_llm(self) -> None:
        if self.llm_provider == "azure":
            thieu = [n for n, v in (("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
                                    ("AZURE_OPENAI_DEPLOYMENT", self.azure_openai_deployment),
                                    ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key)) if not v]
            if thieu:
                raise SystemExit("LLM_PROVIDER=azure nhung thieu bien: " + ", ".join(thieu))
        elif self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                raise SystemExit("LLM_PROVIDER=anthropic nhung thieu ANTHROPIC_API_KEY")
        else:
            raise SystemExit(f"LLM_PROVIDER={self.llm_provider!r} khong hop le, chi nhan azure hoac anthropic")

    @property
    def live_model_name(self) -> str:
        """Ten model dung de ghi so va tinh gia. Tren Azure la ten deployment."""
        return self.azure_openai_deployment if self.llm_provider == "azure" else self.agent_model


settings = Settings()
