import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import Page
from backend.app.config import settings

class ObservationExtractor:
    """Extracts compressed, structured observations and screenshots from active Playwright pages."""

    EXTRACT_ELEMENTS_JS = """
    () => {
        const interactive = [];
        const seen = new Set();
        const elements = document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"], form');
        
        let idx = 0;
        for (const el of elements) {
            if (idx >= 60) break; // Limit element budget for efficiency
            
            const rect = el.getBoundingClientRect();
            const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
            if (!isVisible) continue;

            const tag = el.tagName.toLowerCase();
            const id = el.id || '';
            const name = el.getAttribute('name') || '';
            const type = el.getAttribute('type') || '';
            const role = el.getAttribute('role') || '';
            const placeholder = el.getAttribute('placeholder') || '';
            const href = el.getAttribute('href') || '';
            const value = el.value || '';
            let text = (el.innerText || el.textContent || el.value || placeholder || '').trim();
            // Truncate long innerText
            if (text.length > 80) text = text.substring(0, 77) + '...';

            let selector = '';
            if (id) {
                selector = `#${id}`;
            } else if (name) {
                selector = `${tag}[name="${name}"]`;
            } else if (tag === 'button' && text) {
                selector = `button:has-text("${text.replace(/"/g, '\\\\"')}")`;
            } else if (tag === 'a' && text) {
                selector = `a:has-text("${text.replace(/"/g, '\\\\"')}")`;
            } else {
                selector = `${tag}${el.className ? '.' + Array.from(el.classList).slice(0, 2).join('.') : ''}`;
            }

            if (!seen.has(selector)) {
                seen.add(selector);
                interactive.push({
                    tag,
                    id,
                    name,
                    type,
                    role,
                    text,
                    value,
                    href,
                    selector,
                    is_enabled: !el.disabled,
                    bbox: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
                idx++;
            }
        }
        return interactive;
    }
    """

    EXTRACT_TEXT_JS = """
    () => {
        // Extract visible heading and paragraph text
        const blocks = document.querySelectorAll('h1, h2, h3, h4, p, label, .alert, .error, .message, [role="alert"]');
        const textSnippets = [];
        for (const b of blocks) {
            const txt = (b.innerText || '').trim();
            if (txt && txt.length > 2 && txt.length < 300) {
                textSnippets.push(txt);
            }
        }
        return textSnippets.slice(0, 25).join(' | ');
    }
    """

    @classmethod
    async def capture_observation(
        cls,
        page: Page,
        user_id: str,
        step_number: int,
        take_screenshot: bool = True
    ) -> Dict[str, Any]:
        url = page.url
        try:
            title = await page.title()
        except Exception:
            title = ""

        interactive_elements: List[Dict[str, Any]] = []
        visible_text = ""

        try:
            interactive_elements = await page.evaluate(cls.EXTRACT_ELEMENTS_JS)
        except Exception:
            interactive_elements = []

        try:
            visible_text = await page.evaluate(cls.EXTRACT_TEXT_JS)
        except Exception:
            visible_text = ""

        screenshot_path: Optional[str] = None
        if take_screenshot and settings.RECORD_SCREENSHOTS:
            try:
                screenshot_filename = f"{user_id}_step_{step_number}.png"
                full_path = os.path.join(settings.STORAGE_DIR, screenshot_filename)
                await page.screenshot(path=full_path, full_page=False)
                screenshot_path = f"/screenshots/{screenshot_filename}"
            except Exception:
                screenshot_path = None

        return {
            "url": url,
            "page_title": title,
            "visible_text_summary": visible_text,
            "interactive_elements": interactive_elements,
            "interactive_elements_count": len(interactive_elements),
            "screenshot_path": screenshot_path
        }
