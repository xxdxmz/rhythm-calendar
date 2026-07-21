from backend.bilibili.browser_client import BrowserDynamicClient


def test_clean_rendered_text() -> None:
    assert BrowserDynamicClient._clean_text("公告正文\u200b\n 展开 ") == "公告正文"
    assert BrowserDynamicClient._clean_text("正文\n#Arcaea#") == "正文\n#Arcaea#"
