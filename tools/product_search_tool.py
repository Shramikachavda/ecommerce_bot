from langchain_core.tools import tool
from firebase.firebase_client import FirebaseClient


firebase_client = FirebaseClient()

@tool
def product_search(category: str = None, name_query: str = None, description_query: str = None, price_range: float = None, quantity: int = None) -> list:
    """Search Firestore for products matching category, name, description, price, and quantity.
    
    Args:
        category (str, optional): The product category to filter by.
        name_query (str, optional): A substring to match against product names.
        description_query (str, optional): A substring to match against product descriptions.
        price_range (float, optional): Maximum price to filter by.
        quantity (int, optional): Minimum quantity to filter by.
    
    Returns:
        list: List of product dictionaries from Firestore.
    """
    try:
        # Start with the products collection
        query_ref = firebase_client.get_firestore().collection("products")

        # Apply filters
        if category:
            query_ref = query_ref.where("category", "==", category.capitalize())
        if name_query:
            # Case-insensitive substring match for name (Firestore limitation: exact match only, so filter client-side)
            query_ref = query_ref  # No direct where clause; handle below
        if description_query:
            # Same for description
            query_ref = query_ref  # Handle client-side
        if price_range:
            query_ref = query_ref.where("price", "<=", price_range)
        if quantity:
            query_ref = query_ref.where("quantity", ">=", quantity)

        # Execute query
        results = query_ref.get()
        products = [doc.to_dict() for doc in results]

        # Client-side filtering for name and description (case-insensitive)
        filtered_products = []
        for product in products:
            name_match = not name_query or name_query.lower() in str(product.get("name", "")).lower()
            desc_match = not description_query or description_query.lower() in str(product.get("description", "")).lower()
            if name_match and desc_match:
                filtered_products.append(product)

        print(f"[ProductSearch] {len(filtered_products)} products found with category='{category}', name~'{name_query}', "
              f"description~'{description_query}', price ≤ {price_range}, qty ≥ {quantity}")
        return filtered_products

    except Exception as e:
        print(f"[ProductSearch ERROR] {str(e)}")
        return []