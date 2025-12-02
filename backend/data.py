"""
Updated seed script with suppliers matching the test queries:
- 5,000 meters of organic cotton canvas
- 10k yards of denim fabric
- Cotton poplin 120gsm, GOTS certified
- Polyester blend 50/50, 150gsm, 20,000m
"""

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random

# Database connection
DATABASE_URL = "sqlite:///./suppliers.db"
print(f"Connecting to database at {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True)

def seed_suppliers():
    """Add 25 diverse suppliers matching test queries"""
    
    suppliers_data = [
        # ===== ORGANIC COTTON CANVAS SUPPLIERS (8 suppliers) =====
        {
            "supplier_id": "CANVAS_001",
            "name": "EcoCanvas Mills Turkey",
            "location": "Istanbul, Turkey",
            "email": "igntayyab@gmail.com",
            "phone": "+90-212-555-0101",
            "website": "www.ecocanvas.tr",
            "price_per_unit": 4.80,
            "currency": "USD",
            "lead_time_days": 22,
            "min_order_qty": 3000.0,
            "reputation_score": 8.9,
            "active": True,
            "source": "internal",
            "specialties": "organic cotton,cotton canvas,canvas,sustainable fabrics,eco-friendly",
            "certifications": "GOTS,OEKO-TEX,Fair Trade",
            "notes": "Premium organic cotton canvas, excellent for heavy-duty applications"
        },
        {
            "supplier_id": "CANVAS_002",
            "name": "Canvas Master India",
            "location": "Mumbai, India",
            "email": "export@canvasmaster.in",
            "phone": "+91-22-555-0201",
            "website": "www.canvasmaster.in",
            "price_per_unit": 4.20,
            "currency": "USD",
            "lead_time_days": 28,
            "min_order_qty": 4000.0,
            "reputation_score": 8.5,
            "active": True,
            "source": "internal",
            "specialties": "cotton canvas,organic cotton,canvas fabric,heavy cotton",
            "certifications": "GOTS,ISO 9001,OEKO-TEX",
            "notes": "Cost-effective organic canvas, reliable delivery"
        },
        {
            "supplier_id": "CANVAS_003",
            "name": "Portuguese Canvas Co",
            "location": "Porto, Portugal",
            "email": "contact@portuguesecanvas.pt",
            "phone": "+351-22-555-0301",
            "website": "www.portuguesecanvas.pt",
            "price_per_unit": 5.50,
            "currency": "EUR",
            "lead_time_days": 18,
            "min_order_qty": 2000.0,
            "reputation_score": 9.2,
            "active": True,
            "source": "internal",
            "specialties": "organic cotton,cotton canvas,premium canvas,eco-friendly textiles",
            "certifications": "GOTS,Cradle to Cradle,EU Ecolabel,OEKO-TEX",
            "notes": "Premium European canvas, fast EU shipping"
        },
        {
            "supplier_id": "CANVAS_004",
            "name": "Egyptian Canvas Textiles",
            "location": "Cairo, Egypt",
            "email": "sales@egyptcanvas.eg",
            "phone": "+20-2-555-0401",
            "website": "www.egyptcanvas.eg",
            "price_per_unit": 4.10,
            "currency": "USD",
            "lead_time_days": 25,
            "min_order_qty": 3500.0,
            "reputation_score": 8.3,
            "active": True,
            "source": "internal",
            "specialties": "cotton canvas,egyptian cotton,canvas,organic cotton",
            "certifications": "GOTS,OEKO-TEX",
            "notes": "Famous Egyptian cotton canvas quality"
        },
        {
            "supplier_id": "CANVAS_005",
            "name": "USA Canvas Works",
            "location": "North Carolina, USA",
            "email": "info@usacanvas.us",
            "phone": "+1-919-555-0501",
            "website": "www.usacanvas.us",
            "price_per_unit": 6.20,
            "currency": "USD",
            "lead_time_days": 15,
            "min_order_qty": 2500.0,
            "reputation_score": 8.8,
            "active": True,
            "source": "internal",
            "specialties": "organic cotton,cotton canvas,canvas,premium fabrics,made in USA",
            "certifications": "GOTS,OEKO-TEX,USDA Organic",
            "notes": "Premium US-made organic canvas, fastest delivery"
        },
        {
            "supplier_id": "CANVAS_006",
            "name": "Bangladesh Canvas Export",
            "location": "Dhaka, Bangladesh",
            "email": "export@bdcanvas.com",
            "phone": "+880-2-555-0601",
            "website": "www.bdcanvas.com",
            "price_per_unit": 3.80,
            "currency": "USD",
            "lead_time_days": 32,
            "min_order_qty": 5000.0,
            "reputation_score": 7.9,
            "active": True,
            "source": "internal",
            "specialties": "cotton canvas,canvas fabric,organic cotton,affordable canvas",
            "certifications": "GOTS,ISO 9001",
            "notes": "Budget-friendly canvas option, large capacity"
        },
        {
            "supplier_id": "CANVAS_007",
            "name": "China Canvas Manufacturing",
            "location": "Guangzhou, China",
            "email": "sales@chinacanvas.cn",
            "phone": "+86-20-555-0701",
            "website": "www.chinacanvas.cn",
            "price_per_unit": 3.60,
            "currency": "USD",
            "lead_time_days": 30,
            "min_order_qty": 6000.0,
            "reputation_score": 8.0,
            "active": True,
            "source": "alibaba",
            "specialties": "cotton canvas,canvas,organic cotton,heavy duty canvas",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Verified Alibaba supplier, good volume capacity"
        },
        {
            "supplier_id": "CANVAS_008",
            "name": "Vietnam Canvas Industries",
            "location": "Ho Chi Minh, Vietnam",
            "email": "export@vncanvas.vn",
            "phone": "+84-28-555-0801",
            "website": "www.vncanvas.vn",
            "price_per_unit": 3.90,
            "currency": "USD",
            "lead_time_days": 28,
            "min_order_qty": 4500.0,
            "reputation_score": 8.1,
            "active": True,
            "source": "internal",
            "specialties": "cotton canvas,organic cotton,canvas fabric,sustainable textiles",
            "certifications": "GOTS,OEKO-TEX",
            "notes": "Growing supplier with competitive pricing"
        },
        
        # ===== DENIM SPECIALISTS (6 suppliers) =====
        {
            "supplier_id": "DEN_001",
            "name": "Classic Denim Mills China",
            "location": "Guangzhou, China",
            "email": "export@classicdenim.cn",
            "phone": "+86-20-555-0601",
            "website": "www.classicdenim.cn",
            "price_per_unit": 3.85,
            "currency": "USD",
            "lead_time_days": 30,
            "min_order_qty": 8000.0,
            "reputation_score": 8.1,
            "active": True,
            "source": "alibaba",
            "specialties": "denim,cotton denim,stretch denim,indigo fabrics,denim fabric",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Large capacity denim manufacturer"
        },
        {
            "supplier_id": "DEN_002",
            "name": "Premium Denim Turkey",
            "location": "Bursa, Turkey",
            "email": "sales@premiumdenim.tr",
            "phone": "+90-224-555-0701",
            "website": "www.premiumdenim.tr",
            "price_per_unit": 4.60,
            "currency": "USD",
            "lead_time_days": 24,
            "min_order_qty": 5000.0,
            "reputation_score": 8.7,
            "active": True,
            "source": "internal",
            "specialties": "denim,premium denim,stretch denim,selvedge denim,denim fabric",
            "certifications": "GOTS,OEKO-TEX,BCI",
            "notes": "High-quality Turkish denim"
        },
        {
            "supplier_id": "DEN_003",
            "name": "Bangladesh Denim Co",
            "location": "Dhaka, Bangladesh",
            "email": "export@bddenim.com",
            "phone": "+880-2-555-0801",
            "website": "www.bddenim.com",
            "price_per_unit": 3.50,
            "currency": "USD",
            "lead_time_days": 35,
            "min_order_qty": 9000.0,
            "reputation_score": 7.9,
            "active": True,
            "source": "global_sources",
            "specialties": "denim,cotton denim,affordable denim,bulk denim,denim fabric",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Most competitive pricing"
        },
        {
            "supplier_id": "DEN_004",
            "name": "Italian Denim Masters",
            "location": "Milan, Italy",
            "email": "info@italiandenim.it",
            "phone": "+39-02-555-0901",
            "website": "www.italiandenim.it",
            "price_per_unit": 7.20,
            "currency": "EUR",
            "lead_time_days": 20,
            "min_order_qty": 3000.0,
            "reputation_score": 9.4,
            "active": True,
            "source": "internal",
            "specialties": "premium denim,designer denim,selvedge denim,Italian denim,denim fabric",
            "certifications": "GOTS,OEKO-TEX,Made in Italy",
            "notes": "Luxury denim for high-end brands"
        },
        {
            "supplier_id": "DEN_005",
            "name": "India Denim Works",
            "location": "Ahmedabad, India",
            "email": "sales@indiадenim.in",
            "phone": "+91-79-555-1001",
            "website": "www.indiadenim.in",
            "price_per_unit": 3.70,
            "currency": "USD",
            "lead_time_days": 28,
            "min_order_qty": 10000.0,
            "reputation_score": 8.0,
            "active": True,
            "source": "internal",
            "specialties": "denim,cotton denim,denim fabric,bulk denim",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "High volume capacity"
        },
        {
            "supplier_id": "DEN_006",
            "name": "Pakistan Denim Mills",
            "location": "Karachi, Pakistan",
            "email": "export@pkdenim.pk",
            "phone": "+92-21-555-1101",
            "website": "www.pkdenim.pk",
            "price_per_unit": 3.65,
            "currency": "USD",
            "lead_time_days": 29,
            "min_order_qty": 9500.0,
            "reputation_score": 7.8,
            "active": True,
            "source": "internal",
            "specialties": "denim,cotton denim,denim fabric,affordable denim",
            "certifications": "ISO 9001",
            "notes": "Competitive South Asian supplier"
        },
        
        # ===== COTTON POPLIN 120GSM SUPPLIERS (5 suppliers) =====
        {
            "supplier_id": "POP_001",
            "name": "Global Poplin Textiles",
            "location": "Karachi, Pakistan",
            "email": "sales@globalpoplin.pk",
            "phone": "+92-21-555-1001",
            "website": "www.globalpoplin.pk",
            "price_per_unit": 2.80,
            "currency": "USD",
            "lead_time_days": 26,
            "min_order_qty": 6000.0,
            "reputation_score": 8.0,
            "active": True,
            "source": "internal",
            "specialties": "cotton poplin,poplin 120gsm,poplin,lightweight fabrics,shirting fabrics",
            "certifications": "GOTS,OEKO-TEX,ISO 9001",
            "notes": "Specialized in 120gsm poplin weaves"
        },
        {
            "supplier_id": "POP_002",
            "name": "Fine Cotton Poplin India",
            "location": "Tirupur, India",
            "email": "export@finecotton.in",
            "phone": "+91-421-555-1101",
            "website": "www.finecotton.in",
            "price_per_unit": 2.60,
            "currency": "USD",
            "lead_time_days": 30,
            "min_order_qty": 7000.0,
            "reputation_score": 7.8,
            "active": True,
            "source": "internal",
            "specialties": "cotton poplin,poplin 120gsm,poplin 100gsm,poplin,shirting fabrics",
            "certifications": "GOTS,ISO 9001,OEKO-TEX",
            "notes": "High volume poplin capacity"
        },
        {
            "supplier_id": "POP_003",
            "name": "Euro Poplin Fabrics",
            "location": "Barcelona, Spain",
            "email": "contact@europoplin.es",
            "phone": "+34-93-555-1201",
            "website": "www.europoplin.es",
            "price_per_unit": 3.90,
            "currency": "EUR",
            "lead_time_days": 22,
            "min_order_qty": 4000.0,
            "reputation_score": 8.6,
            "active": True,
            "source": "internal",
            "specialties": "cotton poplin,premium poplin,poplin 120gsm,organic poplin,poplin",
            "certifications": "GOTS,OEKO-TEX,EU Ecolabel",
            "notes": "Premium European poplin 120gsm"
        },
        {
            "supplier_id": "POP_004",
            "name": "Turkey Poplin Export",
            "location": "Istanbul, Turkey",
            "email": "sales@turkeypoplin.tr",
            "phone": "+90-212-555-1301",
            "website": "www.turkeypoplin.tr",
            "price_per_unit": 2.95,
            "currency": "USD",
            "lead_time_days": 24,
            "min_order_qty": 5000.0,
            "reputation_score": 8.2,
            "active": True,
            "source": "internal",
            "specialties": "cotton poplin,poplin 120gsm,poplin,organic poplin",
            "certifications": "GOTS,OEKO-TEX",
            "notes": "Quality Turkish poplin manufacturer"
        },
        {
            "supplier_id": "POP_005",
            "name": "China Poplin Mills",
            "location": "Hangzhou, China",
            "email": "export@chinapoplin.cn",
            "phone": "+86-571-555-1401",
            "website": "www.chinapoplin.cn",
            "price_per_unit": 2.40,
            "currency": "USD",
            "lead_time_days": 28,
            "min_order_qty": 8000.0,
            "reputation_score": 7.7,
            "active": True,
            "source": "alibaba",
            "specialties": "cotton poplin,poplin 120gsm,poplin 100gsm,poplin,affordable poplin",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Cost-effective poplin source"
        },
        
        # ===== POLYESTER BLEND 50/50 150GSM SUPPLIERS (6 suppliers) =====
        {
            "supplier_id": "POLY_001",
            "name": "Synthetic Fabrics China Ltd",
            "location": "Hangzhou, China",
            "email": "sales@syntheticfabrics.cn",
            "phone": "+86-571-555-1301",
            "website": "www.syntheticfabrics.cn",
            "price_per_unit": 2.20,
            "currency": "USD",
            "lead_time_days": 28,
            "min_order_qty": 10000.0,
            "reputation_score": 8.2,
            "active": True,
            "source": "alibaba",
            "specialties": "polyester blend,50/50 blend,cotton polyester,150gsm fabrics,poly cotton blend",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Large-scale polyester blend 150gsm producer"
        },
        {
            "supplier_id": "POLY_002",
            "name": "Blend Masters India",
            "location": "Surat, India",
            "email": "export@blendmasters.in",
            "phone": "+91-261-555-1401",
            "website": "www.blendmasters.in",
            "price_per_unit": 2.10,
            "currency": "USD",
            "lead_time_days": 32,
            "min_order_qty": 12000.0,
            "reputation_score": 7.7,
            "active": True,
            "source": "internal",
            "specialties": "polyester blend,50/50 blend,cotton polyester,affordable blends,150gsm,poly cotton",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Most cost-effective for 20,000m+ orders"
        },
        {
            "supplier_id": "POLY_003",
            "name": "TechFabric Solutions Korea",
            "location": "Seoul, South Korea",
            "email": "info@techfabric.kr",
            "phone": "+82-2-555-1501",
            "website": "www.techfabric.kr",
            "price_per_unit": 3.40,
            "currency": "USD",
            "lead_time_days": 25,
            "min_order_qty": 8000.0,
            "reputation_score": 8.9,
            "active": True,
            "source": "internal",
            "specialties": "polyester blend,premium blends,50/50 blend,technical fabrics,150gsm,poly cotton",
            "certifications": "ISO 9001,OEKO-TEX,Bluesign",
            "notes": "High-tech 150gsm blends, excellent durability"
        },
        {
            "supplier_id": "POLY_004",
            "name": "Vietnam Textile Blends",
            "location": "Ho Chi Minh, Vietnam",
            "email": "sales@vietnamblends.vn",
            "phone": "+84-28-555-1601",
            "website": "www.vietnamblends.vn",
            "price_per_unit": 2.35,
            "currency": "USD",
            "lead_time_days": 30,
            "min_order_qty": 9000.0,
            "reputation_score": 8.0,
            "active": True,
            "source": "global_sources",
            "specialties": "polyester blend,cotton polyester,50/50 blend,150gsm fabrics,poly cotton",
            "certifications": "ISO 9001,OEKO-TEX",
            "notes": "Good quality-price balance for blends"
        },
        {
            "supplier_id": "POLY_005",
            "name": "Pakistan Poly Textiles",
            "location": "Faisalabad, Pakistan",
            "email": "sales@pkpoly.pk",
            "phone": "+92-41-555-1701",
            "website": "www.pkpoly.pk",
            "price_per_unit": 2.15,
            "currency": "USD",
            "lead_time_days": 29,
            "min_order_qty": 15000.0,
            "reputation_score": 7.9,
            "active": True,
            "source": "internal",
            "specialties": "polyester blend,50/50 blend,cotton polyester,150gsm,bulk poly cotton",
            "certifications": "ISO 9001",
            "notes": "Bulk blend supplier, competitive for large orders"
        },
        {
            "supplier_id": "POLY_006",
            "name": "Turkey Blend Industries",
            "location": "Denizli, Turkey",
            "email": "export@turkeyblend.tr",
            "phone": "+90-258-555-1801",
            "website": "www.turkeyblend.tr",
            "price_per_unit": 2.50,
            "currency": "USD",
            "lead_time_days": 26,
            "min_order_qty": 10000.0,
            "reputation_score": 8.3,
            "active": True,
            "source": "internal",
            "specialties": "polyester blend,50/50 blend,premium blends,150gsm,poly cotton blend",
            "certifications": "OEKO-TEX,ISO 9001",
            "notes": "Quality Turkish blends with fast production"
        }
    ]
    
    # Insert suppliers
    with engine.connect() as conn:
        for supplier in suppliers_data:
            insert_query = text("""
                INSERT INTO suppliers 
                (supplier_id, name, location, email, phone, website, price_per_unit, 
                 currency, lead_time_days, min_order_qty, reputation_score, active, 
                 source, specialties, certifications, notes, created_at, updated_at)
                VALUES 
                (:supplier_id, :name, :location, :email, :phone, :website, :price_per_unit,
                 :currency, :lead_time_days, :min_order_qty, :reputation_score, :active,
                 :source, :specialties, :certifications, :notes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            
            conn.execute(insert_query, supplier)
        
        conn.commit()
    
    print(f"✓ Successfully inserted {len(suppliers_data)} suppliers!")
    print(f"\n  - {len([s for s in suppliers_data if 'canvas' in s['specialties'].lower()])} Canvas suppliers")
    print(f"  - {len([s for s in suppliers_data if 'denim' in s['specialties'].lower()])} Denim suppliers")
    print(f"  - {len([s for s in suppliers_data if 'poplin 120gsm' in s['specialties'].lower()])} Poplin 120gsm suppliers")
    print(f"  - {len([s for s in suppliers_data if '150gsm' in s['specialties'].lower()])} Polyester blend 150gsm suppliers")


def seed_performance_data():
    """Add historical performance data for suppliers"""
    
    current_year = datetime.now().year
    
    performance_data = []
    # Get all supplier IDs from the seed data
    supplier_ids = [
        # Canvas
        "CANVAS_001", "CANVAS_002", "CANVAS_003", "CANVAS_004", "CANVAS_005",
        "CANVAS_006", "CANVAS_007", "CANVAS_008",
        # Denim
        "DEN_001", "DEN_002", "DEN_003", "DEN_004", "DEN_005", "DEN_006",
        # Poplin
        "POP_001", "POP_002", "POP_003", "POP_004", "POP_005",
        # Polyester
        "POLY_001", "POLY_002", "POLY_003", "POLY_004", "POLY_005", "POLY_006"
    ]
    
    for supplier_id in supplier_ids:
        # Add 2 quarters of performance data for each supplier
        for quarter in [1, 2]:
            perf = {
                "supplier_id": supplier_id,
                "year": current_year,
                "quarter": quarter,
                "avg_lead_time": random.randint(18, 35),
                "reliability_score": round(random.uniform(7.0, 9.5), 1),
                "avg_price": round(random.uniform(2.0, 6.5), 2),
                "on_time_delivery_rate": round(random.uniform(85.0, 98.0), 1),
                "defect_rate": round(random.uniform(0.5, 3.0), 1),
                "total_orders": random.randint(5, 25),
                "successful_orders": random.randint(4, 24),
                "communication_score": round(random.uniform(7.5, 9.5), 1),
                "quality_score": round(random.uniform(7.0, 9.5), 1)
            }
            performance_data.append(perf)
    
    # Insert performance data
    with engine.connect() as conn:
        for perf in performance_data:
            insert_query = text("""
                INSERT INTO supplier_performance 
                (supplier_id, year, quarter, avg_lead_time, reliability_score, avg_price,
                 on_time_delivery_rate, defect_rate, total_orders, successful_orders,
                 communication_score, quality_score, created_at, updated_at)
                VALUES 
                (:supplier_id, :year, :quarter, :avg_lead_time, :reliability_score, :avg_price,
                 :on_time_delivery_rate, :defect_rate, :total_orders, :successful_orders,
                 :communication_score, :quality_score, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            
            conn.execute(insert_query, perf)
        
        conn.commit()
    
    print(f"✓ Successfully inserted {len(performance_data)} performance records!")


def verify_data():
    """Verify the inserted data"""
    
    with engine.connect() as conn:
        # Count suppliers
        result = conn.execute(text("SELECT COUNT(*) FROM suppliers"))
        supplier_count = result.fetchone()[0]
        print(f"\n✓ Total suppliers in database: {supplier_count}")
        
        # Test the exact queries from DEFAULT_GET_QUOTE_INPUT
        test_queries = [
            ("cotton canvas", "SELECT COUNT(*) FROM suppliers WHERE specialties LIKE '%cotton canvas%' AND active = 1"),
            ("denim fabric", "SELECT COUNT(*) FROM suppliers WHERE specialties LIKE '%denim%' AND active = 1"),
            ("poplin 120gsm", "SELECT COUNT(*) FROM suppliers WHERE specialties LIKE '%poplin 120gsm%' AND active = 1"),
            ("polyester blend 150gsm", "SELECT COUNT(*) FROM suppliers WHERE specialties LIKE '%150gsm%' AND active = 1")
        ]
        
        print("\n📊 Test Query Results:")
        for fabric, query in test_queries:
            result = conn.execute(text(query))
            count = result.fetchone()[0]
            print(f"  ✓ {fabric}: {count} suppliers found")
import os

if __name__ == "__main__":
    print("="*60)
    print("SEEDING SUPPLIER DATABASE (UPDATED)")
    print("="*60)
    
    try:
        print("\n[1/3] Inserting suppliers...")
        seed_suppliers()
        
        print("\n[2/3] Inserting performance data...")
        seed_performance_data()
        
        print("\n[3/3] Verifying data...")
        verify_data()
        
        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETE! ✓")
        print("="*60)
        print("\nYour agent should now find suppliers for:")
        print("  • 5,000 meters of organic cotton canvas → 8 suppliers")
        print("  • 10k yards of denim fabric → 6 suppliers")
        print("  • Cotton poplin 120gsm, GOTS certified → 5 suppliers")
        print("  • Polyester blend 50/50, 150gsm, 20,000m → 6 suppliers")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()