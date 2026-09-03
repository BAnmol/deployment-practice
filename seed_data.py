import os
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
import models
from auth import hash_password

def seed_database(force_reseed=False):
    if force_reseed:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if table columns exist or reseed
        if force_reseed or db.query(models.Product).count() > 0:
            print("Clearing tables and reseeding with complete classic product descriptions and comprehensive reviews...")
            db.query(models.OrderItem).delete()
            db.query(models.Order).delete()
            db.query(models.BasketItem).delete()
            db.query(models.Review).delete()
            db.query(models.Product).delete()
            db.query(models.Coupon).delete()
            db.query(models.User).delete()
            db.commit()

        print("Seeding Indian localized e-commerce database with rich product details and 5-star customer reviews...")

        # 1. Seed Indian Demo Users
        admin_user = models.User(
            email="admin@juice-sh.op",
            password_hash=hash_password("admin123"),
            full_name="Rajesh Verma (Admin)",
            role="admin"
        )
        demo_user = models.User(
            email="customer@juice-sh.op",
            password_hash=hash_password("juice123"),
            full_name="Aarav Sharma",
            role="customer"
        )
        demo_user2 = models.User(
            email="priya@juice-sh.op",
            password_hash=hash_password("juice123"),
            full_name="Priya Patel",
            role="customer"
        )
        db.add_all([admin_user, demo_user, demo_user2])
        db.flush()

        # 2. Seed Indian Promo Coupons
        coupons = [
            models.Coupon(code="DESI10", discount_percent=10.0, max_discount=100.0, is_active=True),
            models.Coupon(code="NAMASTE20", discount_percent=20.0, max_discount=250.0, is_active=True),
            models.Coupon(code="INDIA50", discount_percent=50.0, max_discount=500.0, is_active=True),
            models.Coupon(code="FREESHIP", discount_percent=10.0, max_discount=100.0, is_active=True),
        ]
        db.add_all(coupons)

        # 3. Seed Indian Localized Products with Rich Ingredients, Nutrition, and Origins
        products_data = [
            {
                "name": "Kashmiri Apple Juice (1000ml)",
                "description": "Crisp and refreshing cold-pressed juice extracted from handpicked Red Delicious and Royal Gala apples from the misty orchards of Srinagar, Kashmir. Zero added sugars, 100% raw and unprocessed to preserve vital phytonutrients.",
                "ingredients": "100% Pure Kashmiri Apples (Red Delicious & Royal Gala), Organic Amla Extract, Fresh Himalayan Mint, Natural Vitamin C",
                "nutrition_info": "Calories: 115 kcal | Natural Sugars: 24g (0g Added) | Vitamin C: 48mg (80% RDA) | Potassium: 290mg | Dietary Fiber: 2.5g | Fat: 0g",
                "origin": "Srinagar Orchards, Jammu & Kashmir",
                "shelf_life": "7 Days Refrigerated (0-4°C)",
                "price": 149.00,
                "original_price": 199.00,
                "image_url": "/static/images/apple-juice.svg",
                "category": "Pure Juice",
                "stock": 45,
                "ribbon_badge": "25% OFF",
                "rating": 4.9,
                "review_count": 4,
                "is_featured": True,
            },
            {
                "name": "Ratnagiri Mango & Apple Pomace",
                "description": "Sun-ripened organic fruit fiber and crushed fruit pomace sourced from Ratnagiri Alphonso groves and Himachal hills. Rich in soluble prebiotic pectin, ideal for health smoothies, breakfast oats, and high-fiber baking.",
                "ingredients": "Sun-dried Ratnagiri Alphonso Mango Fiber (60%), Himalayan Golden Apple Pomace (35%), Organic Roasted Flaxseed Powder, Inulin Prebiotic Fiber",
                "nutrition_info": "Calories: 88 kcal | Dietary Fiber: 7.2g (29% RDA) | Natural Sugars: 14g | Vitamin A: 120mcg | Calcium: 45mg",
                "origin": "Ratnagiri, Maharashtra & Solan, HP",
                "shelf_life": "30 Days in Cool Dry Place",
                "price": 79.00,
                "original_price": 99.00,
                "image_url": "/static/images/apple-pomace.svg",
                "category": "Organic Fiber",
                "stock": 80,
                "ribbon_badge": "High Fiber",
                "rating": 4.7,
                "review_count": 3,
                "is_featured": False,
            },
            {
                "name": "Kerala Nendran Banana Juice (1000ml)",
                "description": "Thick, creamy natural nectar made from sun-ripened Kerala Nendran bananas and infused with gentle South Indian green cardamom. Provides instant natural energy and essential muscle-replenishing electrolytes.",
                "ingredients": "Fresh Wayanad Nendran Bananas, Organic Coconut Blossom Nectar, Crushed Green Cardamom Pods, Himalayan Rock Salt, Mineral Spring Water",
                "nutrition_info": "Calories: 142 kcal | Potassium: 480mg (14% RDA) | Vitamin B6: 0.5mg | Natural Carbohydrates: 34g | Magnesium: 38mg",
                "origin": "Wayanad Plantations, Kerala",
                "shelf_life": "5 Days Refrigerated (0-4°C)",
                "price": 129.00,
                "original_price": 159.00,
                "image_url": "/static/images/banana-juice.svg",
                "category": "Pure Juice",
                "stock": 35,
                "ribbon_badge": "Energy Boost",
                "rating": 4.8,
                "review_count": 3,
                "is_featured": True,
            },
            {
                "name": "Fresh Tulsi & Basil Herbal Smoothie",
                "description": "Ancient Ayurvedic rejuvenating detox elixir blended with wild green holy Tulsi, sweet Italian basil leaves, fresh ginger root, and tender baby spinach. Supercharges body immunity and mental focus.",
                "ingredients": "Fresh Holy Tulsi (Ocimum Sanctum), Sweet Italian Basil, Cold-Pressed Green Apple Base, Ginger Rhizome Juice, Baby Spinach, Lemon Zest",
                "nutrition_info": "Calories: 95 kcal | Vitamin C: 65mg (108% RDA) | Iron: 2.1mg | Zinc: 1.4mg | Chlorophyll: 42mg | Total Sugars: 16g",
                "origin": "Herbal Co-op, Haridwar, Uttarakhand",
                "shelf_life": "6 Days Refrigerated (0-4°C)",
                "price": 199.00,
                "original_price": 249.00,
                "image_url": "/static/images/basil-smoothie.svg",
                "category": "Ayurvedic Smoothie",
                "stock": 30,
                "ribbon_badge": "Immunity",
                "rating": 5.0,
                "review_count": 3,
                "is_featured": True,
            },
            {
                "name": "Himalayan Forest Berry Juice (1000ml)",
                "description": "Hand-foraged wild mountain berries gathered from high-altitude Kumaon forests. A vibrant antioxidant fusion of wild blackberries, Mahabaleshwar strawberries, and ruby red pomegranate.",
                "ingredients": "Wild Himalayan Blackberries, Blueberries, Mahabaleshwar Strawberries, Pomegranate Arils Nectar, Red Grape Juice, Vitamin E",
                "nutrition_info": "Calories: 128 kcal | Anthocyanins / Antioxidants: 380mg | Vitamin C: 54mg | Polyphenols: 410mg | Natural Sugars: 26g",
                "origin": "Mukteshwar Hills, Uttarakhand",
                "shelf_life": "7 Days Refrigerated (0-4°C)",
                "price": 249.00,
                "original_price": 299.00,
                "image_url": "/static/images/berry-juice.svg",
                "category": "Pure Juice",
                "stock": 22,
                "ribbon_badge": "Superfood",
                "rating": 5.0,
                "review_count": 3,
                "is_featured": True,
            },
            {
                "name": "OWASP Juice Shop Master Edition",
                "description": "The ultimate holy grail collector's edition! Infused with royal Kashmiri saffron threads, rare cold-pressed wild berries, and 24K edible gold flakes. Comes in a serial-numbered crystal decanter with certificate of authenticity.",
                "ingredients": "Rare 1999 Vintage Fruit Essence, Grade A++ Kashmiri Mongra Saffron, Wild Forest Nectar, 24 Karat Certified Edible Gold Flakes, Royal Citrus Infusion",
                "nutrition_info": "Calories: 210 kcal | Saffron Crocin: 18mg | Royal Elixir Potency: 100% | Pure Luxury: Unlimited",
                "origin": "Master Vault, OWASP Juice Sanctum",
                "shelf_life": "Indefinite Collector's Vintage",
                "price": 99999.00,
                "original_price": 125000.00,
                "image_url": "/static/images/juice-master.svg",
                "category": "Special Collector",
                "stock": 1,
                "ribbon_badge": "Only 1 left",
                "rating": 5.0,
                "review_count": 3,
                "is_featured": True,
            },
            {
                "name": "Desi Delhi Gajar Carrot Juice (1000ml)",
                "description": "Naturally sweet, vibrant red winter carrots from Delhi NCR farmland, slow cold-pressed with aromatic ginger and rock salt. Packed with eye-strengthening Beta-Carotene and natural bioflavonoids.",
                "ingredients": "Fresh Red Winter Carrots (Desi Gajar), Ginger Juice, Fresh Lemon Extract, Himalayan Kala Namak (Black Salt)",
                "nutrition_info": "Calories: 92 kcal | Vitamin A (Beta-Carotene): 950mcg (118% RDA) | Vitamin K: 18mcg | Potassium: 340mg | Sugars: 18g",
                "origin": "Yamuna Basin Farms, Delhi NCR",
                "shelf_life": "6 Days Refrigerated (0-4°C)",
                "price": 169.00,
                "original_price": 199.00,
                "image_url": "/static/images/carrot-juice.svg",
                "category": "Pure Juice",
                "stock": 40,
                "ribbon_badge": "Vitamin A",
                "rating": 4.8,
                "review_count": 3,
                "is_featured": False,
            },
            {
                "name": "Exotic Pitaya Dragon Fruit Lassi",
                "description": "Vibrant magenta smoothie crafted from organic Gujarat pitaya blended with traditional artisanal probiotic curd (A2 Dahi), wildflower honey, and soaked chia seeds. Creamy, tangy, and deeply nourishing.",
                "ingredients": "Fresh Pink Dragon Fruit (Pitaya), Creamy Indian Probiotic A2 Curd (Dahi), Soaked White Chia Seeds, Pure Forest Wild Honey, Cardamom",
                "nutrition_info": "Calories: 165 kcal | Probiotic Live Cultures: 2.5 Billion CFU | Protein: 5.2g | Calcium: 180mg | Vitamin C: 32mg",
                "origin": "Kutch Orchards, Gujarat",
                "shelf_life": "5 Days Refrigerated (0-4°C)",
                "price": 229.00,
                "original_price": 279.00,
                "image_url": "/static/images/dragon-fruit.svg",
                "category": "Ayurvedic Smoothie",
                "stock": 25,
                "ribbon_badge": "Probiotic",
                "rating": 5.0,
                "review_count": 3,
                "is_featured": True,
            },
            {
                "name": "Desi Shikanji Nimbu Paani (1000ml)",
                "description": "Traditional Indian street-style artisanal lemonade crafted with cold-pressed juicy yellow lemons, black rock salt (kala namak), hand-roasted cumin powder, and fresh garden mint. The ultimate Indian summer heatbuster.",
                "ingredients": "Hand-Pressed Maharashtra Lemons, Pure Mineral Water, Roasted Cumin (Bhuna Jeera), Rock Salt (Kala Namak), Fresh Mint Leaves, Organic Khandsari",
                "nutrition_info": "Calories: 72 kcal | Vitamin C: 52mg (86% RDA) | Sodium: 120mg | Potassium: 110mg | Natural Sugars: 14g",
                "origin": "Nashik Citrus Belt, Maharashtra",
                "shelf_life": "7 Days Refrigerated (0-4°C)",
                "price": 99.00,
                "original_price": 129.00,
                "image_url": "/static/images/lemon-juice.svg",
                "category": "Traditional Coolers",
                "stock": 60,
                "ribbon_badge": "Summer Best",
                "rating": 5.0,
                "review_count": 3,
                "is_featured": False,
            },
            {
                "name": "Nagpur Fresh Orange Juice (1000ml)",
                "description": "World-famous GI-tagged sweet & tangy Nagpur mandarin oranges squeezed at gentle 4°C with rich citrus pulp vesicles intact. Delivers 100% natural immunity without any added water, acidity regulators, or preservatives.",
                "ingredients": "100% Pure Squeezed Nagpur Mandarin Oranges with Citrus Pulp (Citrus Reticulata), Natural Orange Oil",
                "nutrition_info": "Calories: 118 kcal | Vitamin C: 82mg (136% RDA) | Folate: 40mcg | Potassium: 380mg | Dietary Fiber: 2.2g | Sugars: 22g",
                "origin": "Katol Groves, Nagpur, Maharashtra",
                "shelf_life": "7 Days Refrigerated (0-4°C)",
                "price": 149.00,
                "original_price": 189.00,
                "image_url": "/static/images/orange-juice.svg",
                "category": "Pure Juice",
                "stock": 55,
                "ribbon_badge": "GI Tagged",
                "rating": 5.0,
                "review_count": 3,
                "is_featured": True,
            }
        ]

        created_products = []
        for p in products_data:
            prod = models.Product(**p)
            db.add(prod)
            created_products.append(prod)

        db.flush()

        # 4. Seed Verified Indian Customer Reviews for ALL 10 Products
        all_reviews_data = [
            # Product 1: Kashmiri Apple Juice
            (created_products[0], "aarav.sharma@mumbai.in", "Aarav Sharma", "Mumbai", 5, 18, "Best apple juice in India! You can genuinely taste the crisp Srinagar apples with zero added sugar. Delivered cold within 30 mins in Mumbai."),
            (created_products[0], "sneha.k@pune.in", "Sneha Kulkarni", "Pune", 5, 12, "The aroma when you open the seal is magical. Extremely fresh, authentic texture and no artificial preservatives. My whole family loves it!"),
            (created_products[0], "rajesh.khanna@delhi.in", "Rajesh Khanna", "New Delhi", 5, 9, "Ordered a 6-pack for my morning workout routine. Clean energy and rich in natural antioxidants."),
            (created_products[0], "meera.s@chennai.in", "Meera Sundaram", "Chennai", 4, 6, "Very refreshing and crisp. Arrived in insulated packaging with ice packs. Highly recommended!"),

            # Product 2: Ratnagiri Mango & Apple Pomace
            (created_products[1], "rohan.deshmukh@ratnagiri.in", "Rohan Deshmukh", "Ratnagiri", 5, 14, "Being from Ratnagiri, I know original Alphonso pulp when I taste it. This organic fiber blend is top notch for breakfast oats and baking!"),
            (created_products[1], "dr.kavita.rao@hyderabad.in", "Dr. Kavita Rao", "Hyderabad", 5, 11, "Excellent source of natural prebiotic pectin. Great for gut health, daily digestion, and cholesterol control."),
            (created_products[1], "amit.joshi@nagpur.in", "Amit Joshi", "Nagpur", 4, 7, "Adds wonderful natural mango aroma and thickness to homemade smoothie bowls. Clean ingredients."),

            # Product 3: Kerala Nendran Banana Juice
            (created_products[2], "anoop.menon@kochi.in", "Anoop Menon", "Kochi", 5, 16, "Authentic Kerala Wayanad Nendran banana flavor with a touch of green cardamom. The ultimate natural post-workout recovery drink."),
            (created_products[2], "deepika.nair@bengaluru.in", "Deepika Nair", "Bengaluru", 5, 13, "Rich, smooth, and very filling. Tastes just like traditional South Indian banana nectar without any watery dilution."),
            (created_products[2], "vinay.hegde@mangaluru.in", "Vinay Hegde", "Mangaluru", 4, 8, "Natural potassium powerhouse. My kids love drinking this before their evening football practice."),

            # Product 4: Fresh Tulsi & Basil Herbal Smoothie
            (created_products[3], "dr_ananya@delhi.gov.in", "Dr. Ananya Iyer", "New Delhi", 5, 24, "The holy Tulsi and ginger combination is magnificent for boosting morning immunity. High quality cold-pressing!"),
            (created_products[3], "gaurav.chawla@chandigarh.in", "Gaurav Chawla", "Chandigarh", 5, 15, "You feel revitalized after just one glass. The green basil aroma is very soothing and the ginger gives a nice pleasant kick."),
            (created_products[3], "pooja.bhatt@dehradun.in", "Pooja Bhatt", "Dehradun", 5, 11, "Fresh herbal goodness straight from Uttarakhand hills. 10/10 recommended for daily detox and mental focus."),

            # Product 5: Himalayan Forest Berry Juice
            (created_products[4], "rohit.verma@bangalore.tech", "Rohit Verma", "Bengaluru", 5, 21, "Very rich Himalayan berry flavor with wild blackberries and strawberries. Paid seamlessly via UPI on PhonePe."),
            (created_products[4], "tanvi.singhal@gurugram.in", "Tanvi Singhal", "Gurugram", 5, 17, "Packed with antioxidants and has a wonderful ruby red color. Tastes luxurious and fresh, not overly sweet."),
            (created_products[4], "karan.kapoor@shimla.in", "Karan Kapoor", "Shimla", 5, 14, "Authentic wild mountain berry notes. Perfect balance of natural tartness and fruity sweetness."),

            # Product 6: OWASP Juice Shop Master Edition
            (created_products[5], "vikramaditya@mumbai.co", "Vikramaditya Singhania", "Mumbai", 5, 42, "Worth every single rupee for true connoisseurs. The 24K gold foil certificate and rare vintage notes make it a museum-grade collector piece!"),
            (created_products[5], "shreya.oberoi@jaipur.in", "Shreya Oberoi", "Jaipur", 5, 31, "A luxurious royal experience beyond words. Kashmiri saffron aroma fills the room as soon as the decanter is opened."),
            (created_products[5], "aditya.birla@kolkata.in", "Aditya Birla", "Kolkata", 5, 28, "The master packaging, heavy crystal decanter, and gold flakes are unmatched. Proud to own bottle #1 of this limited batch."),

            # Product 7: Desi Delhi Gajar Carrot Juice
            (created_products[6], "harpreet.singh@amritsar.in", "Harpreet Singh", "Amritsar", 5, 19, "Tastes exactly like fresh winter red carrots from Punjab and Delhi farms! Kala namak gives it the authentic desi punch."),
            (created_products[6], "neha.gupta@noida.in", "Neha Gupta", "Noida", 5, 14, "High in Beta-carotene, super fresh and sweet without a single grain of added sugar. My go-to breakfast drink."),
            (created_products[6], "rahul.mehra@delhi.in", "Rahul Mehra", "Delhi", 4, 9, "Cold-pressed to perfection. Arrived chilled at 4°C via Swiggy Instamart delivery in under 35 minutes."),

            # Product 8: Exotic Pitaya Dragon Fruit Lassi
            (created_products[7], "jayesh.parekh@ahmedabad.in", "Jayesh Parekh", "Ahmedabad", 5, 23, "The combination of Gujarat dragon fruit and probiotic A2 dahi is pure brilliance. Vibrant magenta color and divine creamy taste!"),
            (created_products[7], "divya.menon@bengaluru.in", "Divya Menon", "Bengaluru", 5, 16, "Chia seeds and wild forest honey add amazing texture. Very refreshing after an evening yoga session."),
            (created_products[7], "sunita.reddy@hyderabad.in", "Sunita Reddy", "Hyderabad", 5, 12, "Creamy, gut-friendly, and ultra delicious. Reordering this every single week!"),

            # Product 9: Desi Shikanji Nimbu Paani
            (created_products[8], "priya.patel@ahmedabad.in", "Priya Patel", "Ahmedabad", 5, 29, "Authentic Desi Shikanji taste with kala namak and roasted bhuna jeera! The best summer heatbuster in India."),
            (created_products[8], "manoj.tiwari@varanasi.in", "Manoj Tiwari", "Varanasi", 5, 20, "Street-style refreshment made completely hygienic with organic lemons and natural Khandsari sugar. Pure nostalgia in every sip."),
            (created_products[8], "suresh.kumar@lucknow.in", "Suresh Kumar", "Lucknow", 5, 15, "Outstanding balance of tangy lemon, rock salt, and mint leaves. Instantly rehydrates in hot weather."),

            # Product 10: Nagpur Fresh Orange Juice
            (created_products[9], "vikram.singh@pune.co", "Vikram Singh", "Nagpur", 5, 35, "Original Nagpur mandarin orange taste with genuine pulp vesicles. Outstanding citrus burst!"),
            (created_products[9], "archana.patil@mumbai.in", "Archana Patil", "Mumbai", 5, 22, "100% pure Vitamin C without any artificial sourness or added water. Kids finished the 1000ml bottle in a day."),
            (created_products[9], "pradeep.shinde@pune.in", "Pradeep Shinde", "Pune", 5, 18, "Fabulous cold-pressed quality. You can clearly see and taste the fresh citrus pulp vesicles in every glass."),
        ]

        for prod, email, name, city, rating, helpful_cnt, comment in all_reviews_data:
            rev = models.Review(
                product_id=prod.id,
                author_email=email,
                author_name=name,
                city=city,
                helpful_count=helpful_cnt,
                rating=rating,
                comment=comment
            )
            db.add(rev)

        # 5. Pre-seed demo basket for demo_user (Aarav Sharma)
        if len(created_products) >= 2:
            item1 = models.BasketItem(
                user_id=demo_user.id,
                product_id=created_products[0].id,
                quantity=1
            )
            item2 = models.BasketItem(
                user_id=demo_user.id,
                product_id=created_products[3].id,
                quantity=1
            )
            db.add_all([item1, item2])

        db.commit()
        print("Database successfully populated with production-level products and verified customer reviews for all items!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database(force_reseed=True)
