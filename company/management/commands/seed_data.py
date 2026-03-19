"""
Management command: python manage.py seed_data

Seeds the database with demo data that mirrors the FinLedger frontend.
Safe to run multiple times — clears and re-seeds.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with FinLedger demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🌱  Seeding FinLedger demo data...'))
        self._create_superuser()
        company = self._create_company()
        groups = self._create_account_groups(company)
        ledgers = self._create_ledgers(company, groups)
        self._create_journal_entries(company, ledgers)
        customers = self._create_customers(company)
        self._create_sales_documents(company, customers)
        vendors = self._create_vendors(company)
        self._create_purchase_orders(company, vendors)
        categories = self._create_categories(company)
        self._create_products(company, categories)
        self.stdout.write(self.style.SUCCESS('✅  Seed complete! Login: admin / admin123'))

    # ── Auth ────────────────────────────────────────────────────────────────

    def _create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@acme.in', 'admin123')
            self.stdout.write('  Created superuser: admin / admin123')

    # ── Company ─────────────────────────────────────────────────────────────

    def _create_company(self):
        from company.models import Company
        company, created = Company.objects.get_or_create(
            name='ACME Industries Pvt. Ltd.',
            defaults={
                'short_name': 'ACME',
                'gstin': '27AABCU9603R1ZP',
                'pan': 'AABCU9603R',
                'address': '123 Industrial Area, Andheri East, Mumbai - 400001, Maharashtra',
                'phone': '+91 22 4567 8900',
                'email': 'accounts@acme.in',
                'fy_start': date(2025, 4, 1),
                'fy_end': date(2026, 3, 31),
                'base_currency': 'INR',
                'gst_scheme': 'Regular',
            }
        )
        if created:
            self.stdout.write(f'  Created company: {company.name}')
        return company

    # ── Account Groups ───────────────────────────────────────────────────────

    def _create_account_groups(self, company):
        from accounts.models import AccountGroup
        data = [
            ('1000', 'Assets', 'Primary', 'Asset', None),
            ('1100', 'Current Assets', 'Sub-Group', 'Asset', '1000'),
            ('1200', 'Fixed Assets', 'Sub-Group', 'Asset', '1000'),
            ('2000', 'Liabilities', 'Primary', 'Liability', None),
            ('2100', 'Current Liabilities', 'Sub-Group', 'Liability', '2000'),
            ('2200', 'Long-Term Liabilities', 'Sub-Group', 'Liability', '2000'),
            ('3000', 'Income', 'Primary', 'Income', None),
            ('3100', 'Direct Income', 'Sub-Group', 'Income', '3000'),
            ('4000', 'Expenses', 'Primary', 'Expense', None),
            ('4100', 'Direct Expenses', 'Sub-Group', 'Expense', '4000'),
        ]
        groups = {}
        for code, name, gtype, nature, parent_code in data:
            parent = groups.get(parent_code)
            g, _ = AccountGroup.objects.get_or_create(
                company=company, code=code,
                defaults={'name': name, 'group_type': gtype, 'nature': nature, 'parent': parent}
            )
            groups[code] = g
        self.stdout.write(f'  Created {len(groups)} account groups')
        return groups

    # ── Ledgers ──────────────────────────────────────────────────────────────

    def _create_ledgers(self, company, groups):
        from accounts.models import Ledger
        data = [
            ('L001', 'Cash', '1100', 145200, 'Dr'),
            ('L002', 'Bank - HDFC', '1100', 892500, 'Dr'),
            ('L003', 'Accounts Receivable', '1100', 234800, 'Dr'),
            ('L004', 'Sales Account', '3100', 1245000, 'Cr'),
            ('L005', 'Purchase Account', '4100', 780000, 'Dr'),
            ('L006', 'Salary Payable', '2100', 85000, 'Cr'),
            ('L007', 'GST Payable', '2100', 42000, 'Cr'),
            ('L008', 'Office Equipment', '1200', 320000, 'Dr'),
        ]
        ledgers = {}
        for lid, name, group_code, balance, btype in data:
            l, _ = Ledger.objects.get_or_create(
                company=company, ledger_id=lid,
                defaults={
                    'name': name,
                    'group': groups[group_code],
                    'balance': Decimal(balance),
                    'balance_type': btype,
                    'opening_balance': Decimal(balance),
                    'opening_balance_type': btype,
                }
            )
            ledgers[lid] = l
        self.stdout.write(f'  Created {len(ledgers)} ledgers')
        return ledgers

    # ── Journal Entries ──────────────────────────────────────────────────────

    def _create_journal_entries(self, company, ledgers):
        from accounts.models import JournalEntry, JournalLine
        entries_data = [
            ('JV-001', 'Receipt', date(2026, 3, 10), 'INV-0041', 'Sales received from XYZ Corp',
             'L002', 'L004', 52000),
            ('JV-002', 'Purchase', date(2026, 3, 9), 'PO-0019', 'Purchase from ABC Suppliers',
             'L005', 'L003', 28500),
            ('JV-003', 'Payment', date(2026, 3, 8), 'SAL-MAR', 'March salary disbursement',
             'L006', 'L001', 85000),
            ('JV-004', 'Payment', date(2026, 3, 7), 'GST-Q4', 'GST payment for Feb quarter',
             'L007', 'L002', 18200),
            ('JV-005', 'Receipt', date(2026, 3, 6), 'POS-220', 'Cash sales - retail counter',
             'L001', 'L004', 12800),
        ]
        for vnum, vtype, vdate, ref, narr, dr_id, cr_id, amt in entries_data:
            if JournalEntry.objects.filter(company=company, voucher_number=vnum).exists():
                continue
            entry = JournalEntry.objects.create(
                company=company,
                voucher_number=vnum,
                voucher_type=vtype,
                date=vdate,
                reference=ref,
                narration=narr,
                is_posted=True,
            )
            JournalLine.objects.create(entry=entry, ledger=ledgers[dr_id], entry_type='Dr', amount=Decimal(amt))
            JournalLine.objects.create(entry=entry, ledger=ledgers[cr_id], entry_type='Cr', amount=Decimal(amt))
        self.stdout.write('  Created 5 journal entries')

    # ── Customers ────────────────────────────────────────────────────────────

    def _create_customers(self, company):
        from sales.models import Customer
        names = ['Apex Technologies', 'GlobalMart Ltd', 'Star Industries',
                 'Nova Corp', 'Pinnacle Pvt Ltd', 'Zenith Solutions', 'Metro Distributors']
        customers = {}
        for name in names:
            c, _ = Customer.objects.get_or_create(company=company, name=name)
            customers[name] = c
        self.stdout.write(f'  Created {len(customers)} customers')
        return customers

    # ── Sales Documents ──────────────────────────────────────────────────────

    def _create_sales_documents(self, company, customers):
        from sales.models import SalesDocument, SalesDocumentLine
        docs_data = [
            ('QT-2026-0041', 'Quotation', date(2026, 3, 10), 'Apex Technologies', 'Pending', 145000),
            ('PI-2026-0028', 'Proforma', date(2026, 3, 9), 'GlobalMart Ltd', 'Approved', 289000),
            ('SO-2026-0067', 'Order', date(2026, 3, 8), 'Star Industries', 'Confirmed', 92500),
            ('DC-2026-0033', 'Challan', date(2026, 3, 7), 'Nova Corp', 'Dispatched', 67000),
            ('INV-2026-0089', 'Invoice', date(2026, 3, 6), 'Pinnacle Pvt Ltd', 'Paid', 178500),
            ('INV-2026-0088', 'Invoice', date(2026, 3, 5), 'Zenith Solutions', 'Overdue', 54200),
            ('QT-2026-0040', 'Quotation', date(2026, 3, 4), 'Metro Distributors', 'Converted', 98700),
        ]
        for doc_num, dtype, ddate, cust_name, dstatus, amount in docs_data:
            if SalesDocument.objects.filter(company=company, doc_number=doc_num).exists():
                continue
            doc = SalesDocument.objects.create(
                company=company,
                doc_type=dtype,
                doc_number=doc_num,
                date=ddate,
                customer=customers[cust_name],
                customer_name=cust_name,
                status=dstatus,
                subtotal=Decimal(amount),
                total_gst=Decimal(0),
                total_amount=Decimal(amount),
            )
            # Add a representative line item
            SalesDocumentLine.objects.create(
                document=doc,
                line_number=1,
                product_name='Industrial Pump A200',
                quantity=Decimal('1'),
                unit='pcs',
                rate=Decimal(amount),
                gst_rate=Decimal('18'),
            )
        self.stdout.write('  Created 7 sales documents')

    # ── Vendors ──────────────────────────────────────────────────────────────

    def _create_vendors(self, company):
        from purchase.models import Vendor
        names = ['ABC Suppliers', 'XYZ Wholesale', 'Global Traders', 'Rapid Supplies']
        vendors = {}
        for name in names:
            v, _ = Vendor.objects.get_or_create(company=company, name=name)
            vendors[name] = v
        self.stdout.write(f'  Created {len(vendors)} vendors')
        return vendors

    # ── Purchase Orders ──────────────────────────────────────────────────────

    def _create_purchase_orders(self, company, vendors):
        from purchase.models import PurchaseOrder, PurchaseOrderLine
        po_data = [
            ('PO-2026-0019', date(2026, 3, 9), 'ABC Suppliers', 'Received', 28500, 8),
            ('PO-2026-0018', date(2026, 3, 7), 'XYZ Wholesale', 'Pending', 67200, 15),
            ('PI-2026-0012', date(2026, 3, 5), 'Global Traders', 'Paid', 124000, 22),
            ('PO-2026-0017', date(2026, 3, 3), 'Rapid Supplies', 'Partial', 45800, 6),
        ]
        for po_num, po_date, vname, vstatus, amount, items in po_data:
            if PurchaseOrder.objects.filter(company=company, po_number=po_num).exists():
                continue
            po = PurchaseOrder.objects.create(
                company=company,
                po_number=po_num,
                date=po_date,
                vendor=vendors[vname],
                vendor_name=vname,
                status=vstatus,
                subtotal=Decimal(amount),
                total_gst=Decimal(0),
                total_amount=Decimal(amount),
            )
            PurchaseOrderLine.objects.create(
                purchase_order=po,
                line_number=1,
                product_name='Steel Pipe 2"',
                quantity=Decimal(items),
                unit='pcs',
                rate=Decimal(amount) / items,
                gst_rate=Decimal('18'),
            )
        self.stdout.write('  Created 4 purchase orders')

    # ── Categories & Products ────────────────────────────────────────────────

    def _create_categories(self, company):
        from inventory.models import Category
        names = ['Machinery', 'Electronics', 'Raw Material', 'Components']
        categories = {}
        for name in names:
            c, _ = Category.objects.get_or_create(company=company, name=name)
            categories[name] = c
        self.stdout.write(f'  Created {len(categories)} categories')
        return categories

    def _create_products(self, company, categories):
        from inventory.models import Product
        products_data = [
            ('SKU-001', 'Industrial Pump A200', 'Machinery', 24, 10, 12500, 18000, 'pcs'),
            ('SKU-002', 'Control Panel v3', 'Electronics', 8, 15, 8200, 11500, 'pcs'),
            ('SKU-003', 'Steel Pipe 2"', 'Raw Material', 450, 100, 280, 420, 'mtrs'),
            ('SKU-004', 'Safety Valve SV10', 'Components', 62, 20, 1800, 2600, 'pcs'),
            ('SKU-005', 'Bearing Set BRG-22', 'Components', 5, 25, 650, 950, 'sets'),
        ]
        for sku, name, cat, stock, min_stock, cost, price, unit in products_data:
            Product.objects.get_or_create(
                company=company, sku=sku,
                defaults={
                    'name': name,
                    'category': categories[cat],
                    'stock_quantity': Decimal(stock),
                    'min_stock_level': Decimal(min_stock),
                    'cost_price': Decimal(cost),
                    'selling_price': Decimal(price),
                    'mrp': Decimal(price),
                    'unit': unit,
                    'gst_rate': Decimal('18'),
                }
            )
        self.stdout.write('  Created 5 products')
