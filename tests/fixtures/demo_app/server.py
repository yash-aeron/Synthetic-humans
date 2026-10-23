from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional

app = FastAPI(title="Synthetix Electronics - Toy Target Application")

PRODUCTS = [
    {
        "id": "laptop-pro-15",
        "name": "OmniBook Pro 15",
        "category": "laptops",
        "price": "$1,299",
        "description": "High performance workstation with 32GB RAM and 1TB NVMe storage."
    },
    {
        "id": "laptop-air-13",
        "name": "OmniBook Air 13",
        "category": "laptops",
        "price": "$999",
        "description": "Ultra-portable lightweight laptop with all-day battery life."
    },
    {
        "id": "tablet-x",
        "name": "TabSlate Ultra",
        "category": "tablets",
        "price": "$649",
        "description": "Crisp OLED display for creative workflows."
    }
]

HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Synthetix Hardware</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background: #f8fafc; color: #0f172a; line-height: 1.5; }}
        header {{ background: #1e293b; color: #ffffff; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        header a {{ color: #ffffff; text-decoration: none; margin-right: 1.5rem; font-weight: 500; font-size: 0.95rem; }}
        header a:hover {{ text-decoration: underline; }}
        .container {{ max-width: 1000px; margin: 2rem auto; padding: 0 1.5rem; }}
        .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .btn {{ display: inline-block; background: #2563eb; color: #ffffff; padding: 0.6rem 1.2rem; border-radius: 4px; text-decoration: none; border: none; cursor: pointer; font-weight: 500; font-size: 0.95rem; }}
        .btn:hover {{ background: #1d4ed8; }}
        .btn-secondary {{ background: #64748b; }}
        .btn-secondary:hover {{ background: #475569; }}
        .alert {{ background: #fee2e2; border: 1px solid #f87171; color: #b91c1c; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1rem; font-size: 0.9rem; }}
        .success-box {{ background: #ecfdf5; border: 1px solid #34d399; color: #065f46; padding: 2rem; border-radius: 6px; text-align: center; }}
        .form-group {{ margin-bottom: 1.25rem; }}
        .form-group label {{ display: block; font-weight: 500; margin-bottom: 0.4rem; font-size: 0.9rem; }}
        .form-control {{ width: 100%; padding: 0.6rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 0.95rem; }}
        .search-bar {{ display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }}
        .search-bar input {{ flex: 1; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }}
        /* Usability Trap 1: Extra vertical spacing pushing CTA far down */
        .spacer-tall {{ height: 280px; }}
        .helper-text {{ font-size: 0.85rem; color: #64748b; margin-top: 0.3rem; }}
    </style>
</head>
<body>
    <header>
        <div style="font-weight: 700; font-size: 1.2rem;"><a href="/">Synthetix Hardware</a></div>
        <nav>
            <a href="/">Home</a>
            <!-- Usability Trap 3: Category menu leads to intermediate looping index -->
            <a href="/category/computing" id="nav-computing">Computing Systems</a>
            <a href="/products" id="nav-catalog">Products Catalog</a>
            <a href="/cart" id="nav-cart">Cart (<span id="cart-count">0</span>)</a>
        </nav>
    </header>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def landing():
    content = """
    <div class="card" style="text-align: center; padding: 3rem 1.5rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 1rem;">Next-Generation Portable Workstations</h1>
        <p style="color: #64748b; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Explore our precision laptops, mobile workstations, and high-performance computing hardware.
        </p>
        <div style="display: flex; justify-content: center; gap: 1rem;">
            <a href="/products?category=laptops" id="hero-laptops" class="btn">Explore Laptops</a>
            <a href="/category/computing" id="hero-info" class="btn btn-secondary">System Specifications FAQ</a>
        </div>
    </div>

    <div class="search-bar">
        <form action="/products" method="get" style="display: flex; width: 100%; gap: 0.5rem;">
            <input type="text" name="q" id="search-input" class="form-control" placeholder="Search laptops, tablets, hardware...">
            <button type="submit" id="search-button" class="btn">Search</button>
        </form>
    </div>
    """
    return HTML_BASE.format(title="Home", content=content)

@app.get("/category/computing", response_class=HTMLResponse)
async def computing_category_intermediate():
    # USABILITY ISSUE 3: Intermediate category page with ambiguous links that loops users back to home
    content = """
    <div class="card">
        <h2>Computing Systems Architecture Index</h2>
        <p style="color: #64748b; margin: 1rem 0;">
            Welcome to the system architecture directory. Please select your orientation profile to proceed.
        </p>
        <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
            <a href="/" id="btn-return-overview" class="btn btn-secondary">Return to General Hardware Overview</a>
            <a href="/products?category=laptops" id="btn-view-models" class="btn">View Production Notebook Models</a>
        </div>
    </div>
    """
    return HTML_BASE.format(title="Computing Architecture", content=content)

@app.get("/products", response_class=HTMLResponse)
async def products_catalog(q: Optional[str] = None, category: Optional[str] = None):
    filtered = PRODUCTS
    if q:
        filtered = [p for p in filtered if q.lower() in p["name"].lower() or q.lower() in p["description"].lower()]
    if category:
        filtered = [p for p in filtered if p["category"] == category]

    cards_html = ""
    for p in filtered:
        cards_html += f"""
        <div class="card" style="margin-bottom: 0;">
            <h3 style="margin-bottom: 0.5rem;">{p['name']}</h3>
            <div style="font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 0.75rem;">{p['price']}</div>
            <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem;">{p['description']}</p>
            <a href="/product/{p['id']}" id="view-{p['id']}" class="btn">View Details & Order</a>
        </div>
        """

    if not cards_html:
        cards_html = "<div class='card'><p>No matching products found. Try adjusting your search query.</p></div>"

    content = f"""
    <h2 style="margin-bottom: 1.5rem;">Hardware Catalog</h2>
    <div class="search-bar">
        <form action="/products" method="get" style="display: flex; width: 100%; gap: 0.5rem;">
            <input type="text" name="q" id="catalog-search" class="form-control" value="{q or ''}" placeholder="Search products...">
            <button type="submit" id="catalog-search-btn" class="btn">Filter</button>
        </form>
    </div>
    <div class="grid">
        {cards_html}
    </div>
    """
    return HTML_BASE.format(title="Product Catalog", content=content)

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_details(product_id: str):
    product = next((p for p in PRODUCTS if p["id"] == product_id), PRODUCTS[0])
    content = f"""
    <div class="card">
        <h2>{product['name']}</h2>
        <div style="font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0 1rem 0;">{product['price']}</div>
        <p style="color: #475569; margin-bottom: 1.5rem;">{product['description']}</p>
        
        <form action="/cart/add" method="post">
            <input type="hidden" name="product_id" value="{product['id']}">
            <div class="form-group" style="max-width: 200px;">
                <label for="quantity">Quantity</label>
                <select name="quantity" id="quantity" class="form-control">
                    <option value="1">1 Unit</option>
                    <option value="2">2 Units</option>
                </select>
            </div>
            
            <button type="submit" id="add-to-cart-btn" class="btn" style="background: #16a34a;">Add to Cart</button>
        </form>
    </div>
    """
    return HTML_BASE.format(title=product["name"], content=content)

@app.post("/cart/add")
async def add_to_cart(product_id: str = Form(...), quantity: int = Form(1)):
    return RedirectResponse(url=f"/cart?added={product_id}", status_code=303)

@app.get("/cart", response_class=HTMLResponse)
async def view_cart(added: Optional[str] = None):
    # USABILITY ISSUE 1: The primary proceed to checkout action is pushed below tall vertical padding
    # and has a confusing non-standard label: "Review & Finalize Inquiry"
    content = f"""
    <div class="card">
        <h2>Shopping Cart</h2>
        <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
            <thead>
                <tr style="border-bottom: 2px solid #e2e8f0; text-align: left;">
                    <th style="padding: 0.75rem 0;">Item</th>
                    <th style="padding: 0.75rem 0;">Qty</th>
                    <th style="padding: 0.75rem 0;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 0.75rem 0; font-weight: 500;">OmniBook Pro 15</td>
                    <td style="padding: 0.75rem 0;">1</td>
                    <td style="padding: 0.75rem 0;">$1,299</td>
                </tr>
            </tbody>
        </table>

        <!-- Intentional Usability Obstacle: Extra height pushing button below fold for lower viewports -->
        <div style="margin: 2rem 0; padding: 1rem; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 4px;">
            <p style="font-size: 0.85rem; color: #64748b;">
                Manufacturer Notice: Delivery schedules subject to regional distribution center capacity.
                Please ensure postal zoning is verified during step 2.
            </p>
        </div>

        <div style="text-align: right; margin-top: 1.5rem;">
            <!-- Ambiguous label 'Review & Finalize Inquiry' instead of 'Proceed to Checkout' -->
            <a href="/checkout" id="checkout-btn" class="btn">Review & Finalize Inquiry</a>
        </div>
    </div>
    """
    return HTML_BASE.format(title="Your Cart", content=content)

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_form(error: Optional[str] = None):
    error_box = ""
    if error:
        # USABILITY ISSUE 2: Vague error message that fails to tell the user what format is expected
        error_box = f"""
        <div class="alert" id="form-error">
            <strong>Input Error:</strong> Validation Check 4B Failed on Postal Routing Code.
        </div>
        """

    content = f"""
    <div class="card" style="max-width: 600px; margin: 0 auto;">
        <h2>Order Information & Delivery</h2>
        <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem;">
            Please enter delivery contact credentials. No credit card required for research demo.
        </p>

        {error_box}

        <form action="/checkout" method="post">
            <div class="form-group">
                <label for="full_name">Full Name</label>
                <input type="text" id="full_name" name="full_name" class="form-control" value="Alex Mercer" required>
            </div>

            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" class="form-control" value="alex@example.com" required>
            </div>

            <div class="form-group">
                <label for="street">Street Address</label>
                <input type="text" id="street" name="street" class="form-control" value="100 Silicon Way" required>
            </div>

            <div class="form-group">
                <label for="zip_code">Postal Code / ZIP</label>
                <!-- Strict validation without clear hint -->
                <input type="text" id="zip_code" name="zip_code" class="form-control" placeholder="Postal Code" required>
                <div class="helper-text">Enter regional postal routing index.</div>
            </div>

            <div style="margin-top: 2rem;">
                <button type="submit" id="submit-order-btn" class="btn" style="width: 100%; background: #16a34a;">
                    Confirm & Complete Order
                </button>
            </div>
        </form>
    </div>
    """
    return HTML_BASE.format(title="Checkout", content=content)

@app.post("/checkout")
async def process_checkout(
    full_name: str = Form(...),
    email: str = Form(...),
    street: str = Form(...),
    zip_code: str = Form(...)
):
    clean_zip = zip_code.strip()
    # USABILITY ISSUE 2 validation check: Only accepts strictly 5 digit numerical codes like '94105'
    if not (clean_zip.isdigit() and len(clean_zip) == 5):
        return RedirectResponse(url="/checkout?error=validation_failed", status_code=303)

    return RedirectResponse(url="/order-placed", status_code=303)

@app.get("/order-placed", response_class=HTMLResponse)
async def order_placed():
    content = """
    <div class="card success-box">
        <h1 style="color: #065f46; margin-bottom: 1rem;">Order Confirmed!</h1>
        <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
            Thank you for your purchase inquiry. Your simulated order #SYN-84920 has been placed successfully.
        </p>
        <p style="color: #047857; font-size: 0.95rem; margin-bottom: 2rem;">
            A confirmation receipt has been dispatched to your email address.
        </p>
        <a href="/" class="btn" style="background: #059669;">Return to Storefront</a>
    </div>
    """
    return HTML_BASE.format(title="Order Confirmed", content=content)
