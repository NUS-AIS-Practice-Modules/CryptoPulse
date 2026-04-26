from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from .docx_links import extract_docx_links


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print DOCX web links to local PDFs.")
    parser.add_argument("--links-docx", required=True, help="DOCX file containing URLs")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered PDFs")
    parser.add_argument("--manifest", required=True, help="JSONL output manifest")
    parser.add_argument("--limit", type=int, default=0, help="Optional URL limit")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    args = parser.parse_args(argv)

    links = extract_docx_links(args.links_docx)
    if args.limit > 0:
        links = links[: args.limit]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    records = _download_links_as_pdfs(
        links,
        output_dir=output_dir,
        overwrite=args.overwrite,
        timeout_ms=args.timeout_ms,
    )

    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    ok_count = sum(1 for record in records if record["status"] == "ok")
    print(f"urls={len(records)} pdfs={ok_count} manifest={manifest_path}")
    return 0 if ok_count == len(records) else 1


def _download_links_as_pdfs(
    links: list[str],
    *,
    output_dir: Path,
    overwrite: bool,
    timeout_ms: int,
) -> list[dict]:
    from playwright.sync_api import sync_playwright

    records: list[dict] = []
    with sync_playwright() as p:
        browser = _launch_browser(p)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.set_default_timeout(timeout_ms)

        for index, url in enumerate(links, start=1):
            pdf_path = output_dir / f"{index:02d}-{_slug_for_url(url)}.pdf"
            record = {
                "url": url,
                "path": str(pdf_path),
                "source": "news",
                "published_at": "",
                "metadata": {
                    "source_id": _source_id_for_url(url),
                    "url": url,
                    "language": "en",
                    "entity_tags": [],
                    "ingested_at": _utc_now(),
                },
                "status": "pending",
                "title": "",
            }

            try:
                if not pdf_path.exists() or overwrite:
                    _prepare_report_page(page, url, timeout_ms)
                    download_url = _find_direct_report_pdf_url(page, url)
                    if download_url and _save_pdf_from_url(page, download_url, pdf_path):
                        record["download_url"] = download_url
                        record["acquisition_method"] = "direct_pdf"
                    elif _click_download_button(page, pdf_path):
                        record["acquisition_method"] = "browser_download"
                    else:
                        _hide_print_overlays(page)
                        _print_pdf(page, pdf_path)
                        record["acquisition_method"] = "printed_page"
                else:
                    _prepare_report_page(page, url, timeout_ms)
                record["title"] = page.title() or _title_from_url(url)
                record["status"] = "ok"
            except Exception as exc:  # noqa: BLE001 - persist failures in manifest.
                record["status"] = "error"
                record["error"] = str(exc)
            records.append(record)

        browser.close()
    return records


def _prepare_report_page(page, url: str, timeout_ms: int) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    _settle_network(page, timeout_ms)
    _handle_report_overlays(page)
    _settle_network(page, timeout_ms)
    page.emulate_media(media="screen")


def _handle_report_overlays(page) -> None:
    _click_button_by_text(page, ("ALLOW ALL", "Allow all", "Accept all", "ACCEPT ALL", "Accept"))
    page.wait_for_timeout(750)

    if _has_visible_text(page, "INVESTOR PROFILE"):
        _select_country(page, ("United States", "USA", "US"))
        if _has_visible_text(page, "not available") or _has_visible_text(page, "not supported"):
            _select_country(page, ("Spain", "Spanish", "España"))
        _click_button_by_text(page, ("CONFIRM", "Confirm", "Continue"))
        page.wait_for_timeout(750)

    _click_button_by_text(page, ("Close banner", "Continue", "I agree"))
    page.wait_for_timeout(500)


def _find_direct_report_pdf_url(page, page_url: str) -> str | None:
    candidates = page.evaluate(
        """
        () => Array.from(document.querySelectorAll('a')).map((anchor) => ({
          text: (anchor.innerText || anchor.textContent || '').trim().replace(/\\s+/g, ' '),
          href: anchor.href || anchor.getAttribute('href') || '',
          className: String(anchor.className || '')
        })).filter((item) => {
          const haystack = `${item.text} ${item.href} ${item.className}`.toLowerCase();
          return haystack.includes('download') ||
                 haystack.includes('full report') ||
                 haystack.includes('/d/insights/');
        })
        """
    )
    for candidate in candidates:
        href = candidate.get("href", "")
        text = candidate.get("text", "").lower()
        class_name = candidate.get("className", "").lower()
        if not href:
            continue
        if (
            "/d/insights/" in href
            or "download" in text
            or "full report" in text
            or "richtext-report" in class_name
        ):
            return urljoin(page_url, href)
    return None


def _save_pdf_from_url(page, url: str, pdf_path: Path) -> bool:
    try:
        response = page.context.request.get(url, timeout=60000)
        body = response.body()
    except Exception:
        return False

    content_type = response.headers.get("content-type", "").lower()
    if response.status != 200:
        return False
    if "application/pdf" not in content_type and not body.startswith(b"%PDF"):
        return False

    pdf_path.write_bytes(body)
    return True


def _click_download_button(page, pdf_path: Path) -> bool:
    locators = [
        "a.richtext-report__link",
        "text=/download the full report/i",
        "text=/download/i",
    ]
    for selector in locators:
        try:
            locator = page.locator(selector).first
            if not locator.count() or not locator.is_visible():
                continue
            with page.expect_download(timeout=15000) as download_info:
                locator.click(timeout=5000)
            download = download_info.value
            download.save_as(str(pdf_path))
            return True
        except Exception:
            continue
    return False


def _select_country(page, country_names: tuple[str, ...]) -> bool:
    try:
        selector = page.locator(".ui-select-country").first
        if selector.count() and selector.is_visible():
            selector.click(timeout=1500)
            page.wait_for_timeout(300)
    except Exception:
        return False

    for country_name in country_names:
        if _click_text_if_visible(page, country_name):
            page.wait_for_timeout(500)
            return True
    return False


def _click_button_by_text(page, texts: tuple[str, ...]) -> bool:
    for text in texts:
        clicked = page.evaluate(
            """
            (label) => {
              const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
              const target = buttons.find((button) =>
                (button.innerText || button.textContent || '').trim().toLowerCase() === label.toLowerCase()
              );
              if (target) {
                target.click();
                return true;
              }
              return false;
            }
            """,
            text,
        )
        if clicked:
            return True
    return False


def _has_visible_text(page, text: str) -> bool:
    try:
        locator = page.get_by_text(text, exact=False).first
        return bool(locator.count() and locator.is_visible())
    except Exception:
        return False


def _click_if_visible(page, selector: str) -> bool:
    try:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            locator.click(timeout=1500)
            return True
    except Exception:
        return False
    return False


def _click_text_if_visible(page, text: str) -> bool:
    try:
        locator = page.get_by_text(text, exact=True).first
        if locator.count() and locator.is_visible():
            locator.click(timeout=1500)
            return True
    except Exception:
        return False
    return False


def _hide_print_overlays(page) -> None:
    page.evaluate(
        """
        () => {
          const selectors = [
            '#CybotCookiebotDialog',
            '#CybotCookiebotDialogBodyUnderlay',
            '#CybotCookiebotBanner',
            '.CybotCookiebotDialog',
            '.CybotCookiebotBanner',
            '.welcomePopup',
            '.investorProfileAlert',
            '.profileAlert',
            '.profileBanner',
            '[class*="welcomePopup"]',
            '[class*="investor-profile" i]',
            '[class*="profile-alert" i]',
            '[class*="profile-banner" i]'
          ];
          for (const selector of selectors) {
            for (const element of document.querySelectorAll(selector)) {
              element.remove();
            }
          }
        }
        """
    )
    page.add_style_tag(
        content="""
        #CybotCookiebotDialog,
        #CybotCookiebotDialogBodyUnderlay,
        #CybotCookiebotDialogDetail,
        #CybotCookiebotDialogPoweredByText,
        #CybotCookiebotDialogPoweredbyLink,
        #CybotCookiebotBanner,
        .CybotCookiebotDialog,
        .CybotCookiebotDialogContentWrapper,
        .CybotCookiebotBanner,
        .CookieConsent,
        .cookie-banner,
        .cookies,
        .welcomePopup,
        .welcomePopup *,
        .investorProfileAlert,
        .profileAlert,
        .profileBanner,
        [class*="welcomePopup"],
        [class*="investor-profile" i],
        [class*="profile-alert" i],
        [class*="profile-banner" i],
        [id*="cookie" i],
        [class*="cookie" i],
        [id*="consent" i],
        [class*="consent" i] {
          display: none !important;
          visibility: hidden !important;
          opacity: 0 !important;
          pointer-events: none !important;
        }
        body {
          overflow: visible !important;
        }
        """
    )


def _settle_network(page, timeout_ms: int) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 15000))
    except Exception:
        page.wait_for_timeout(1500)


def _print_pdf(page, pdf_path: Path) -> None:
    page.pdf(
        path=str(pdf_path),
        format="A4",
        print_background=True,
        margin={
            "top": "12mm",
            "bottom": "12mm",
            "left": "10mm",
            "right": "10mm",
        },
    )


def _launch_browser(playwright):
    chrome_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome_path.exists():
        return playwright.chromium.launch(
            executable_path=str(chrome_path),
            headless=True,
        )
    return playwright.chromium.launch(headless=True)


def _slug_for_url(url: str) -> str:
    parsed = urlparse(url)
    value = f"{parsed.netloc}-{parsed.path.strip('/') or 'index'}"
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:110] or "web-page"


def _source_id_for_url(url: str) -> str:
    parsed = urlparse(url)
    return _slug_for_url(f"{parsed.netloc}{parsed.path}")


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.strip("/").replace("-", " ").replace("_", " ") or parsed.netloc


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
