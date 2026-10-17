from typing import Dict, Any, Optional

class HierarchicalTaskPlanner:
    """Decomposes structured user goals into situational subgoals based on page observation."""

    PAGE_PATTERNS = {
        "success": ["confirmation", "thank-you", "success", "order-placed", "complete"],
        "checkout": ["checkout", "payment", "review-order", "billing"],
        "cart": ["cart", "basket", "bag"],
        "product_detail": ["product/", "item/", "details", "p/"],
        "product_list": ["products", "catalog", "category", "search"],
        "landing": ["/", "home", "index"]
    }

    @classmethod
    def identify_page_context(cls, url: str, title: str) -> str:
        url_lower = url.lower()
        title_lower = title.lower()

        for page_type, keywords in cls.PAGE_PATTERNS.items():
            for kw in keywords:
                if kw in url_lower or kw in title_lower:
                    return page_type
        return "unknown"

    @classmethod
    def update_subgoal(cls, current_goal: str, url: str, title: str, observation: Dict[str, Any]) -> str:
        page_ctx = cls.identify_page_context(url, title)

        if page_ctx == "success":
            return "verify_completion"
        elif page_ctx == "checkout":
            return "submit_checkout_form"
        elif page_ctx == "cart":
            return "proceed_to_checkout"
        elif page_ctx == "product_detail":
            return "add_to_cart"
        elif page_ctx == "product_list":
            return "choose_target_item"
        else:
            return "discover_products_or_search"
