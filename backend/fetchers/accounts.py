from backend.accounts import ACCOUNTS, GameAccount
from backend.bilibili import BilibiliClient, BilibiliError, BrowserDynamicClient, Dynamic


def fetch_account_dynamics(
    account: GameAccount,
    client: BilibiliClient | None = None,
    browser_client: BrowserDynamicClient | None = None,
) -> list[Dynamic]:
    raw_root = f"data/raw/{account.name}"
    api_client = client or BilibiliClient(raw_dir=raw_root)
    try:
        items = api_client.get_user_dynamic(account.uid)
    except BilibiliError as api_error:
        try:
            browser = browser_client or BrowserDynamicClient(raw_dir=f"{raw_root}/browser")
            items = browser.get_user_dynamic(account.uid)
        except BilibiliError as browser_error:
            raise BilibiliError(
                f"API collection failed: {api_error}; browser fallback failed: {browser_error}"
            ) from browser_error
    else:
        if not items or any(not item.text.strip() for item in items):
            browser = browser_client or BrowserDynamicClient(raw_dir=f"{raw_root}/browser")
            items = browser.get_user_dynamic(account.uid)
    if not items:
        raise BilibiliError(f"Bilibili returned an empty feed for {account.account_name}")
    return sorted(items, key=lambda item: item.publish_time, reverse=True)


def configured_accounts() -> tuple[GameAccount, ...]:
    return ACCOUNTS
