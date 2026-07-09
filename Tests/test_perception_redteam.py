# tests/test_perception_redteam.py

SPOOFED_RESPONSES = [
    {"status": "SUCCESS", "data": [{"nav": "0.0001", "date": "08-07-2026"}]},   # implausible crash
    {"status": "SUCCESS", "data": [{"nav": "999999.99", "date": "08-07-2026"}]},  # implausible spike
    {"status": "SUCCESS", "data": [{"nav": None, "date": "08-07-2026"}]},        # malformed
]

def test_update_navs_rejects_spoofed_feed(monkeypatch, tool_registry):
    for spoofed in SPOOFED_RESPONSES:
        monkeypatch.setattr(
            tool_registry.mFetcher, "get_latest_nav",
            lambda scheme_code: {"nav": None if spoofed["data"][0]["nav"] is None
                                        else float(spoofed["data"][0]["nav"]),
                                  "date": spoofed["data"][0]["date"], "fund_name": "TEST"}
        )
        result = tool_registry.get("update_navs").func(owner_name="SG")
        assert result["updated"] == 0  # nothing malicious should land in holdings
        assert result["rejected"] or result["failures"]