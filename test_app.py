from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    # 1. Test Products endpoint
    res = client.get('/api/products')
    assert res.status_code == 200, f"Status: {res.status_code}"
    products = res.json()
    print(f"Products count: {len(products)}")
    assert len(products) >= 8

    # 2. Test Single Product Detail
    prod_id = products[0]['id']
    res = client.get(f'/api/products/{prod_id}')
    assert res.status_code == 200
    prod_name = res.json()["name"]
    print(f"Product detail fetched: {prod_name}")

    # 3. Test Basket Endpoint
    res = client.get('/api/basket')
    assert res.status_code == 200
    basket = res.json()
    print(f"Initial basket subtotal: {basket['subtotal']}")

    # 4. Test Add to Basket
    res = client.post('/api/basket/add', json={'product_id': prod_id, 'quantity': 2})
    assert res.status_code == 200
    basket = res.json()
    print(f"Updated basket count: {basket['item_count']}, total: {basket['total']}")

    # 5. Test Coupon Application (DESI10)
    res = client.post('/api/basket/coupon', json={'code': 'DESI10'})
    assert res.status_code == 200
    assert res.json()['valid'] == True
    print(f"Coupon status: {res.json()}")


    # 6. Test Login
    res = client.post('/api/auth/login', json={'email': 'customer@juice-sh.op', 'password': 'juice123'})
    assert res.status_code == 200
    token_data = res.json()
    print(f"Login successful for: {token_data['user']['email']}")
    token = token_data['access_token']

    # 7. Test Unauthenticated Checkout (Must fail with 401 Unauthorized)
    guest_client = TestClient(app)
    checkout_payload = {
        'customer_name': 'Anonymous Guest',
        'email': 'guest@example.com',
        'address': '123 Fake Street',
        'city': 'Metropolis',
        'zip_code': '10001',
        'payment_method': 'Credit Card'
    }
    res_unauth = guest_client.post('/api/checkout/process', json=checkout_payload)
    assert res_unauth.status_code == 401, f"Expected 401 Unauthorized without login, got: {res_unauth.status_code}"
    print("Unauthenticated checkout correctly rejected with 401 Unauthorized!")


    # 8. Test Authenticated Dummy Checkout / Payment
    checkout_payload_auth = {
        'customer_name': 'Sarah Squeezer',
        'email': 'customer@juice-sh.op',
        'address': '742 Evergreen Juice Terrace',
        'city': 'Springfield',
        'zip_code': '97477',
        'country': 'United States',
        'delivery_method': 'Fast Track Express',
        'delivery_fee': 1.99,
        'coupon_code': 'JUICE10',
        'payment_method': 'Credit Card',
        'card_details': {
            'card_number': '4532 8901 2345 6789',
            'card_holder': 'SARAH SQUEEZER',
            'expiry': '12/28',
            'cvv': '888'
        }
    }
    # Add item to user's cart
    client.post('/api/basket/add', headers={'Authorization': f'Bearer {token}'}, json={'product_id': prod_id, 'quantity': 1})
    res = client.post('/api/checkout/process', headers={'Authorization': f'Bearer {token}'}, json=checkout_payload_auth)
    assert res.status_code == 200, f"Checkout failed: {res.text}"
    order = res.json()
    print(f"Authenticated Dummy Payment Order processed! Order number: {order['order_number']}, Total: {order['total']}")


    # 8. Test HTML pages
    res_index = client.get('/')
    assert res_index.status_code == 200
    res_login = client.get('/login')
    assert res_login.status_code == 200

    print("=== ALL 8 TEST SUITES PASSED WITH 100% SUCCESS! ===")

if __name__ == '__main__':
    run_tests()
