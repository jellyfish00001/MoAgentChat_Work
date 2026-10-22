"""Azure AD Client Credentials → APIM → AzureChatOpenAI (single factory)."""

from __future__ import annotations

import sys

from azure.identity import ClientSecretCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI

from flows.config.settings import get_settings


def get_access_token() -> str:
    settings = get_settings()
    missing = [
        name
        for name, value in (
            ("AZ_TENANT_ID", settings.az_tenant_id),
            ("AZ_CLIENT_ID", settings.az_client_id),
            ("AZ_CLIENT_SECRET", settings.az_client_secret),
            ("AZ_SCOPE", settings.az_scope),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Azure env vars: {', '.join(missing)}")

    credential = ClientSecretCredential(
        tenant_id=settings.az_tenant_id,
        client_id=settings.az_client_id,
        client_secret=settings.az_client_secret,
    )
    token = credential.get_token(settings.az_scope)
    return token.token


def get_chat_model(*, temperature: float = 0.2) -> AzureChatOpenAI:
    """Build the shared chat model.

    Corporate APIM expects Bearer AAD token + Ocp-Apim-Subscription-Key.
    use_responses_api=False keeps traffic on chat/completions (company gateway).
    """
    settings = get_settings()
    if not settings.az_llm_endpoint or not settings.llm_model_name:
        raise RuntimeError("AZ_LLM_ENDPOINT and LLM_MODEL_NAME are required")

    missing = [
        name
        for name, value in (
            ("AZ_TENANT_ID", settings.az_tenant_id),
            ("AZ_CLIENT_ID", settings.az_client_id),
            ("AZ_CLIENT_SECRET", settings.az_client_secret),
            ("AZ_SCOPE", settings.az_scope),
            ("OCP_APIM_SUBSCRIPTION_KEY", settings.ocp_apim_subscription_key),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Azure/APIM env vars: {', '.join(missing)}")

    credential = ClientSecretCredential(
        tenant_id=settings.az_tenant_id,
        client_id=settings.az_client_id,
        client_secret=settings.az_client_secret,
    )

    return AzureChatOpenAI(
        azure_endpoint=settings.az_llm_endpoint.rstrip("/"),
        api_key="fakekey",
        azure_ad_token_provider=get_bearer_token_provider(
            credential, settings.az_scope
        ),
        api_version=settings.az_llm_version,
        azure_deployment=settings.llm_model_name,
        model=settings.llm_model_name,
        default_headers={
            "Ocp-Apim-Subscription-Key": settings.ocp_apim_subscription_key,
        },
        use_responses_api=False,
        temperature=temperature,
        max_retries=2,
        timeout=60,
    )


def smoke_invoke(prompt: str = "只回覆 OK") -> str:
    model = get_chat_model(temperature=0)
    result = model.invoke(prompt)
    content = result.content
    if isinstance(content, list):
        return str(content)
    return str(content)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    prompt = args[0] if args else "只回覆 OK"
    try:
        text = smoke_invoke(prompt)
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
