from math import inf, nan

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.timezone import now
from hypothesis import given, example
from hypothesis.extra.django import TestCase
from hypothesis.strategies import characters, text, emails, integers, floats, composite

from invoice.models import Address, Customer, Vendor, InvoiceItem, Invoice


class AddAddressViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('address-add')

    @given(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1))
    @example("Main Street", "45", "Capital", "Mainland")
    @example(street='0', number='0', city='0', country='\r', ).xfail(reason='"\r" is not a '
                                                                            'valid input.')
    def test_add_address(self, street, number, city, country):
        response = self.client.post(self.url, data={
            'street': street,
            'number': number,
            'city': city,
            'country': country
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/addresses/')
        address = Address.objects.get(street=street, number=number)
        self.assertIsNotNone(address)
        self.assertEqual(address.city, city)
        self.assertEqual(address.country, country)


class AddCustomerViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('customer-add')

    @given(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           emails())
    @example("John", "Doe", "john@doe.com")
    def test_add_customer(self, first_name, last_name, email):
        address = Address.objects.create(street="Main Street", number="45", city="Capital",
                                         country="Mainland")
        response = self.client.post(self.url, data={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'address': 1
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/customers/')
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        self.assertIsNotNone(customer)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)


class AddVendorViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('vendor-add')

    @given(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           )
    @example("John", "Doe Company")
    def test_add_vendor(self, name, company):
        address = Address.objects.create(street="Main Street", number="45", city="Capital",
                                         country="Mainland")
        response = self.client.post(self.url, data={
            'name': name,
            'company_name': company,
            'address': 1
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/vendors/')
        vendor = Vendor.objects.get(name=name)
        self.assertIsNotNone(vendor)
        self.assertEqual(vendor.company_name, company)
        self.assertEqual(vendor.address, address)


@composite
def build_invoice_item(draw, invoice: Invoice):
    name = draw(text())
    description = draw(text())
    quantity = draw(integers())
    price = draw(floats(allow_infinity=False, allow_nan=False))
    tax = draw(floats(min_value=0.0, max_value=1.0))
    return InvoiceItem(name=name, description=description, quantity=quantity,
                       price=price, tax=tax, invoice=invoice)


class InvoiceItemModelTestCase(TestCase):
    def setUp(self):
        vendor = Vendor()
        customer = Customer()
        self.invoice = Invoice(invoice_number=1, vendor=vendor, customer=customer)

    @given(text(), text(), integers(), floats(allow_infinity=False, allow_nan=False),
           floats(min_value=0.0, max_value=1.0))
    @example('Security Services', 'Implementation of a firewall', 1, 100.0, 0.19)
    def test_create_invoice_item(self, name, description, quantity, price, tax):
        invoice_item = InvoiceItem(name=name, description=description, quantity=quantity,
                                   price=price, tax=tax, invoice=self.invoice)
        self.assertEqual(invoice_item.name, name)
        self.assertEqual(invoice_item.description, description)
        self.assertEqual(invoice_item.quantity, quantity)
        self.assertEqual(invoice_item.price, price)
        self.assertEqual(invoice_item.tax, tax)
        self.assertEqual(invoice_item.net_total, price * quantity)
        self.assertEqual(invoice_item.total, price * quantity * (1.0 + tax))

    def test_negative_tax(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=100.0, tax=-0.19, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_high_tax(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=100.0, tax=1.19, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_inf_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=inf, tax=0.19, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_nan_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=nan, tax=0.19, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_negative_quantity(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=-1,
                                   price=100.0, tax=0.19, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

class InvoiceModelTestCase(TestCase):
    def setUp(self):
        address = Address.objects.create()
        _ = Vendor.objects.create(address=address)
        _ = Customer.objects.create(address=address)

    def test_invoice_items(self):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        invoice_item = build_invoice_item(invoice=invoice).example()
        invoice_item.save()
        self.assertEqual(invoice.items, [invoice_item])
