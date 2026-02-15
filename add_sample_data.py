<<<<<<< HEAD
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from core.models import Category, Product, StockMovement
from django.contrib.auth.models import User
from django.db.models import F, Sum
from django.utils import timezone

# Get admin user (yung ginawa mong superuser)
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    # Kung walang superuser, kunin na lang ang unang user
    admin_user = User.objects.first()
    if not admin_user:
        print("❌ WALANG USER! Gumawa muna ng superuser gamit ang: python manage.py createsuperuser")
        exit()

print("=" * 60)
print("ADDING SAMPLE DATA TO DISKARTENG PINOY INVENTORY SYSTEM")
print("=" * 60)

# ============================================
# MAG-ADD NG MGA CATEGORIES (Kung wala pa)
# ============================================
categories = [
    'GENERATOR', 
    'GRASS CUTTER', 
    'GRINDER', 
    'DRILL', 
    'SAW', 
    'WELDER', 
    'COMPRESSOR', 
    'WATER PUMP'
]

print("\n📁 CHECKING CATEGORIES...")
for cat_name in categories:
    category, created = Category.objects.get_or_create(name=cat_name)
    if created:
        print(f"  ✓ Added category: {cat_name}")
    else:
        print(f"  ✓ Category exists: {cat_name}")

# ============================================
# MAG-ADD NG MGA PRODUCTS
# ============================================
products_data = [
    # (name, sku, category_name, quantity, price)
    # GENERATOR
    ('Honda EU2200i Generator', 'GEN-HND-001', 'GENERATOR', 5, 25000),
    ('Yamaha EF3000 Generator', 'GEN-YAM-001', 'GENERATOR', 3, 32000),
    
    # GRASS CUTTER
    ('Stihl FS 450 Grass Cutter', 'GRC-STH-001', 'GRASS CUTTER', 4, 8500),
    ('Echo SRM-300 Grass Cutter', 'GRC-ECH-001', 'GRASS CUTTER', 6, 7200),
    
    # GRINDER
    ('Bosch GWS 1000 Grinder', 'GRD-BOS-001', 'GRINDER', 8, 3200),
    ('Makita 9556NB Grinder', 'GRD-MAK-001', 'GRINDER', 10, 2800),
    
    # DRILL
    ('Makita 10mm Drill', 'DRL-MKT-001', 'DRILL', 15, 1800),
    ('Bosch 13mm Drill', 'DRL-BOS-001', 'DRILL', 12, 2200),
    
    # SAW
    ('Dewalt Circular Saw', 'SAW-DEW-001', 'SAW', 5, 5500),
    ('Skilsaw Worm Drive', 'SAW-SKL-001', 'SAW', 3, 6800),
    
    # WELDER
    ('Lincoln Welder 220V', 'WEL-LIN-001', 'WELDER', 2, 15000),
    ('Miller Welder 250V', 'WEL-MIL-001', 'WELDER', 2, 18500),
    
    # COMPRESSOR
    ('Air Compressor 25L', 'CMP-001', 'COMPRESSOR', 4, 8500),
    
    # WATER PUMP
    ('Water Pump 1HP', 'PUM-001', 'WATER PUMP', 6, 3200),
]

print("\n📦 ADDING PRODUCTS...")
product_count = 0
for name, sku, cat_name, qty, price in products_data:
    try:
        category = Category.objects.get(name=cat_name)
        product, created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'quantity': qty,
                'price': price,
                'reorder_level': 2,
                'unit': 'pcs'
            }
        )
        if created:
            print(f"  ✓ Added: {name} ({cat_name}) - ₱{price} - Stock: {qty}")
            product_count += 1
        else:
            print(f"  ⚠ Already exists: {name}")
    except Category.DoesNotExist:
        print(f"  ❌ Category not found: {cat_name}")

print(f"\n✅ Total products added: {product_count}")

# ============================================
# MAG-ADD NG STOCK OUT TRANSACTIONS
# ============================================
stock_outs = [
    ('GEN-HND-001', 2, 'SALE-001'),   # Honda Generator
    ('GEN-YAM-001', 1, 'SALE-001'),   # Yamaha Generator
    ('GRC-STH-001', 1, 'SALE-002'),   # Stihl Grass Cutter
    ('GRC-ECH-001', 2, 'SALE-002'),   # Echo Grass Cutter
    ('GRD-BOS-001', 3, 'SALE-003'),   # Bosch Grinder
    ('GRD-MAK-001', 4, 'SALE-003'),   # Makita Grinder
    ('DRL-MKT-001', 5, 'SALE-004'),   # Makita Drill
    ('DRL-BOS-001', 3, 'SALE-004'),   # Bosch Drill
    ('SAW-DEW-001', 2, 'SALE-005'),   # Dewalt Saw
    ('WEL-LIN-001', 1, 'SALE-006'),   # Lincoln Welder
]

print("\n📤 ADDING STOCK OUT TRANSACTIONS...")
stock_out_count = 0
total_stock_out_value = 0

for sku, qty, ref in stock_outs:
    try:
        product = Product.objects.get(sku=sku)
        if product.quantity >= qty:
            # Create stock out movement
            movement = StockMovement.objects.create(
                product=product,
                movement_type='OUT',
                quantity=qty,
                price_at_movement=product.price,
                total_value=qty * product.price,
                reference=ref,
                performed_by=admin_user,
                date=timezone.now()
            )
            # Update product quantity
            product.quantity -= qty
            product.save()
            
            print(f"  ✓ Stock Out: {product.name} - {qty} pcs (₱{movement.total_value}) - {ref}")
            stock_out_count += 1
            total_stock_out_value += movement.total_value
        else:
            print(f"  ⚠ Not enough stock: {product.name} (Available: {product.quantity}, Requested: {qty})")
    except Product.DoesNotExist:
        print(f"  ❌ Product not found: {sku}")

print(f"\n✅ Total stock out transactions: {stock_out_count}")
print(f"✅ Total stock out value: ₱{total_stock_out_value}")

# ============================================
# MAG-ADD NG STOCK IN TRANSACTIONS (Optional)
# ============================================
print("\n📥 ADDING STOCK IN TRANSACTIONS...")
stock_ins = [
    ('CMP-001', 2, 'PO-001'),   # Additional Compressors
    ('PUM-001', 3, 'PO-002'),   # Additional Water Pumps
]

for sku, qty, ref in stock_ins:
    try:
        product = Product.objects.get(sku=sku)
        movement = StockMovement.objects.create(
            product=product,
            movement_type='IN',
            quantity=qty,
            price_at_movement=product.price,
            total_value=qty * product.price,
            reference=ref,
            performed_by=admin_user,
            date=timezone.now()
        )
        product.quantity += qty
        product.save()
        print(f"  ✓ Stock In: {product.name} - +{qty} pcs (₱{movement.total_value}) - {ref}")
    except Product.DoesNotExist:
        print(f"  ❌ Product not found: {sku}")

# ============================================
# I-DISPLAY ANG BUOD
# ============================================
print("\n" + "=" * 60)
print("📊 DATABASE SUMMARY")
print("=" * 60)

# Bilangin ang lahat
total_categories = Category.objects.count()
total_products = Product.objects.count()
total_items = Product.objects.aggregate(total=Sum('quantity'))['total'] or 0
total_stock_movements = StockMovement.objects.count()
total_stock_out = StockMovement.objects.filter(movement_type='OUT').aggregate(total=Sum('total_value'))['total'] or 0
total_inventory_value = Product.objects.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0

print(f"📁 Categories: {total_categories}")
print(f"📦 Products: {total_products}")
print(f"🔢 Total Items in Stock: {total_items}")
print(f"💰 Total Inventory Value: ₱{total_inventory_value:,.2f}")
print(f"📤 Total Stock Out Value: ₱{total_stock_out:,.2f}")
print(f"📋 Total Stock Movements: {total_stock_movements}")

print("\n" + "=" * 60)
print("✅ SAMPLE DATA ADDED SUCCESSFULLY!")
print("=" * 60)
print("\n🌐 Go to: http://127.0.0.1:8000/reports/inventory/")
=======
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from core.models import Category, Product, StockMovement
from django.contrib.auth.models import User
from django.db.models import F, Sum
from django.utils import timezone

# Get admin user (yung ginawa mong superuser)
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    # Kung walang superuser, kunin na lang ang unang user
    admin_user = User.objects.first()
    if not admin_user:
        print("❌ WALANG USER! Gumawa muna ng superuser gamit ang: python manage.py createsuperuser")
        exit()

print("=" * 60)
print("ADDING SAMPLE DATA TO DISKARTENG PINOY INVENTORY SYSTEM")
print("=" * 60)

# ============================================
# MAG-ADD NG MGA CATEGORIES (Kung wala pa)
# ============================================
categories = [
    'GENERATOR', 
    'GRASS CUTTER', 
    'GRINDER', 
    'DRILL', 
    'SAW', 
    'WELDER', 
    'COMPRESSOR', 
    'WATER PUMP'
]

print("\n📁 CHECKING CATEGORIES...")
for cat_name in categories:
    category, created = Category.objects.get_or_create(name=cat_name)
    if created:
        print(f"  ✓ Added category: {cat_name}")
    else:
        print(f"  ✓ Category exists: {cat_name}")

# ============================================
# MAG-ADD NG MGA PRODUCTS
# ============================================
products_data = [
    # (name, sku, category_name, quantity, price)
    # GENERATOR
    ('Honda EU2200i Generator', 'GEN-HND-001', 'GENERATOR', 5, 25000),
    ('Yamaha EF3000 Generator', 'GEN-YAM-001', 'GENERATOR', 3, 32000),
    
    # GRASS CUTTER
    ('Stihl FS 450 Grass Cutter', 'GRC-STH-001', 'GRASS CUTTER', 4, 8500),
    ('Echo SRM-300 Grass Cutter', 'GRC-ECH-001', 'GRASS CUTTER', 6, 7200),
    
    # GRINDER
    ('Bosch GWS 1000 Grinder', 'GRD-BOS-001', 'GRINDER', 8, 3200),
    ('Makita 9556NB Grinder', 'GRD-MAK-001', 'GRINDER', 10, 2800),
    
    # DRILL
    ('Makita 10mm Drill', 'DRL-MKT-001', 'DRILL', 15, 1800),
    ('Bosch 13mm Drill', 'DRL-BOS-001', 'DRILL', 12, 2200),
    
    # SAW
    ('Dewalt Circular Saw', 'SAW-DEW-001', 'SAW', 5, 5500),
    ('Skilsaw Worm Drive', 'SAW-SKL-001', 'SAW', 3, 6800),
    
    # WELDER
    ('Lincoln Welder 220V', 'WEL-LIN-001', 'WELDER', 2, 15000),
    ('Miller Welder 250V', 'WEL-MIL-001', 'WELDER', 2, 18500),
    
    # COMPRESSOR
    ('Air Compressor 25L', 'CMP-001', 'COMPRESSOR', 4, 8500),
    
    # WATER PUMP
    ('Water Pump 1HP', 'PUM-001', 'WATER PUMP', 6, 3200),
]

print("\n📦 ADDING PRODUCTS...")
product_count = 0
for name, sku, cat_name, qty, price in products_data:
    try:
        category = Category.objects.get(name=cat_name)
        product, created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'quantity': qty,
                'price': price,
                'reorder_level': 2,
                'unit': 'pcs'
            }
        )
        if created:
            print(f"  ✓ Added: {name} ({cat_name}) - ₱{price} - Stock: {qty}")
            product_count += 1
        else:
            print(f"  ⚠ Already exists: {name}")
    except Category.DoesNotExist:
        print(f"  ❌ Category not found: {cat_name}")

print(f"\n✅ Total products added: {product_count}")

# ============================================
# MAG-ADD NG STOCK OUT TRANSACTIONS
# ============================================
stock_outs = [
    ('GEN-HND-001', 2, 'SALE-001'),   # Honda Generator
    ('GEN-YAM-001', 1, 'SALE-001'),   # Yamaha Generator
    ('GRC-STH-001', 1, 'SALE-002'),   # Stihl Grass Cutter
    ('GRC-ECH-001', 2, 'SALE-002'),   # Echo Grass Cutter
    ('GRD-BOS-001', 3, 'SALE-003'),   # Bosch Grinder
    ('GRD-MAK-001', 4, 'SALE-003'),   # Makita Grinder
    ('DRL-MKT-001', 5, 'SALE-004'),   # Makita Drill
    ('DRL-BOS-001', 3, 'SALE-004'),   # Bosch Drill
    ('SAW-DEW-001', 2, 'SALE-005'),   # Dewalt Saw
    ('WEL-LIN-001', 1, 'SALE-006'),   # Lincoln Welder
]

print("\n📤 ADDING STOCK OUT TRANSACTIONS...")
stock_out_count = 0
total_stock_out_value = 0

for sku, qty, ref in stock_outs:
    try:
        product = Product.objects.get(sku=sku)
        if product.quantity >= qty:
            # Create stock out movement
            movement = StockMovement.objects.create(
                product=product,
                movement_type='OUT',
                quantity=qty,
                price_at_movement=product.price,
                total_value=qty * product.price,
                reference=ref,
                performed_by=admin_user,
                date=timezone.now()
            )
            # Update product quantity
            product.quantity -= qty
            product.save()
            
            print(f"  ✓ Stock Out: {product.name} - {qty} pcs (₱{movement.total_value}) - {ref}")
            stock_out_count += 1
            total_stock_out_value += movement.total_value
        else:
            print(f"  ⚠ Not enough stock: {product.name} (Available: {product.quantity}, Requested: {qty})")
    except Product.DoesNotExist:
        print(f"  ❌ Product not found: {sku}")

print(f"\n✅ Total stock out transactions: {stock_out_count}")
print(f"✅ Total stock out value: ₱{total_stock_out_value}")

# ============================================
# MAG-ADD NG STOCK IN TRANSACTIONS (Optional)
# ============================================
print("\n📥 ADDING STOCK IN TRANSACTIONS...")
stock_ins = [
    ('CMP-001', 2, 'PO-001'),   # Additional Compressors
    ('PUM-001', 3, 'PO-002'),   # Additional Water Pumps
]

for sku, qty, ref in stock_ins:
    try:
        product = Product.objects.get(sku=sku)
        movement = StockMovement.objects.create(
            product=product,
            movement_type='IN',
            quantity=qty,
            price_at_movement=product.price,
            total_value=qty * product.price,
            reference=ref,
            performed_by=admin_user,
            date=timezone.now()
        )
        product.quantity += qty
        product.save()
        print(f"  ✓ Stock In: {product.name} - +{qty} pcs (₱{movement.total_value}) - {ref}")
    except Product.DoesNotExist:
        print(f"  ❌ Product not found: {sku}")

# ============================================
# I-DISPLAY ANG BUOD
# ============================================
print("\n" + "=" * 60)
print("📊 DATABASE SUMMARY")
print("=" * 60)

# Bilangin ang lahat
total_categories = Category.objects.count()
total_products = Product.objects.count()
total_items = Product.objects.aggregate(total=Sum('quantity'))['total'] or 0
total_stock_movements = StockMovement.objects.count()
total_stock_out = StockMovement.objects.filter(movement_type='OUT').aggregate(total=Sum('total_value'))['total'] or 0
total_inventory_value = Product.objects.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0

print(f"📁 Categories: {total_categories}")
print(f"📦 Products: {total_products}")
print(f"🔢 Total Items in Stock: {total_items}")
print(f"💰 Total Inventory Value: ₱{total_inventory_value:,.2f}")
print(f"📤 Total Stock Out Value: ₱{total_stock_out:,.2f}")
print(f"📋 Total Stock Movements: {total_stock_movements}")

print("\n" + "=" * 60)
print("✅ SAMPLE DATA ADDED SUCCESSFULLY!")
print("=" * 60)
print("\n🌐 Go to: http://127.0.0.1:8000/reports/inventory/")
>>>>>>> 634131f0d28304ffc716afc7bc8862b73380b9a2
print("🌐 Go to: http://127.0.0.1:8000/reports/stock-out/")