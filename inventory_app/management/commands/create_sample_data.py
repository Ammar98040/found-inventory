from django.core.management.base import BaseCommand
from inventory_app.models import Warehouse, Location, Product
import random


class Command(BaseCommand):
    help = 'Create sample data for warehouse'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # إنشاء مستودع (6 صفوف × 15 عمود)
        warehouse, created = Warehouse.objects.get_or_create(
            name='Main Warehouse',
            defaults={
                'description': 'Main warehouse for products',
                'rows_count': 6,
                'columns_count': 15
            }
        )
        
        if created:
            self.stdout.write(f'Created warehouse: ID {warehouse.pk}')
        
        # تحديث الأبعاد إذا تغيرت
        warehouse.rows_count = 6
        warehouse.columns_count = 15
        warehouse.save()
        
        # إنشاء الشبكة الكاملة (6 صفوف × 15 عمود)
        locations_created = 0
        for row in range(1, 7):  # 1 to 6
            for col in range(1, 16):  # 1 to 15
                location, created = Location.objects.get_or_create(
                    warehouse=warehouse,
                    row=row,
                    column=col,
                    defaults={
                        'notes': f'Location R{row}C{col}'
                    }
                )
                if created:
                    locations_created += 1
        
        self.stdout.write(f'Created {locations_created} locations')
        
        # إنشاء منتجات تجريبية
        products_to_create = [
            {'number': 'BAG-001', 'name': 'Sports Bag - Cotton', 'category': 'Sports'},
            {'number': 'BAG-002', 'name': 'Hand Bag - Leather', 'category': 'Handbags'},
            {'number': 'BAG-003', 'name': 'Backpack - Travel', 'category': 'Travel'},
            {'number': 'BAG-004', 'name': 'Laptop Bag', 'category': 'Tech'},
            {'number': 'BAG-005', 'name': 'Shopping Bag - Foldable', 'category': 'Shopping'},
            {'number': 'BAG-006', 'name': 'School Bag - Fabric', 'category': 'School'},
            {'number': 'BAG-007', 'name': 'Hand Bag - Silk', 'category': 'Handbags'},
            {'number': 'BAG-008', 'name': 'Sports Bag - Nylon', 'category': 'Sports'},
            {'number': 'BAG-009', 'name': 'Backpack - Unicorn', 'category': 'Backpacks'},
            {'number': 'BAG-010', 'name': 'Small Bag - Classic', 'category': 'Classic'},
            {'number': 'BAG-011', 'name': 'Hand Bag - White', 'category': 'Handbags'},
            {'number': 'BAG-012', 'name': 'Travel Bag - Large', 'category': 'Travel'},
            {'number': 'BAG-013', 'name': 'Laptop Bag - Waterproof', 'category': 'Tech'},
            {'number': 'BAG-014', 'name': 'School Bag - Foam', 'category': 'School'},
            {'number': 'BAG-015', 'name': 'Hand Bag - Gold Chain', 'category': 'Handbags'},
        ]
        
        created_count = 0
        all_locations = list(Location.objects.filter(warehouse=warehouse))
        
        for i, prod_data in enumerate(products_to_create):
            try:
                # إنشاء المنتج
                product, created = Product.objects.get_or_create(
                    product_number=prod_data['number'],
                    defaults={
                        'name': prod_data['name'],
                        'category': prod_data['category'],
                        'quantity': 10 + (i * 2),
                    }
                )
                
                created_count += 1
                
                # ربط المنتج بموقع عشوائي
                if all_locations:
                    location = random.choice(all_locations)
                    product.location = location
                    product.save()
                    
            except Exception as e:
                self.stdout.write(f'Error creating product {prod_data["number"]}: {e}')
                continue
        
        self.stdout.write(f'Processed {created_count} products')
        self.stdout.write('')
        self.stdout.write('Done! You can now:')
        self.stdout.write('  1. Login to admin panel')
        self.stdout.write('  2. Add more products')
        self.stdout.write('  3. Test the search system')
        self.stdout.write('  4. Go to /manage/ to manage warehouse grid')
