"""账单应用安全与数据一致性测试：越权封堵、余额一致性、转账、跨账本注入、批量操作、分页。

测试缝（公共 HTTP 接口）：/api/accounts/transfer/、/api/bills/ 各 action。
"""
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient

from .models import Book, Account, Category, Tag, Bill, update_account_balance


class BillBase(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pass')
        self.bob = User.objects.create_user('bob', password='pass')

        self.a_book = Book.objects.create(owner=self.alice, name='A账本')
        self.a_book2 = Book.objects.create(owner=self.alice, name='A2账本')
        self.b_book = Book.objects.create(owner=self.bob, name='B账本')

        # 与 API 行为一致：新建账户时 balance = initial_balance
        self.a_cash = Account.objects.create(book=self.a_book, name='现金', initial_balance=Decimal('100'), balance=Decimal('100'))
        self.a_wx = Account.objects.create(book=self.a_book, name='微信', initial_balance=Decimal('50'), balance=Decimal('50'))
        self.a_other = Account.objects.create(book=self.a_book2, name='其他账本账户')
        self.b_cash = Account.objects.create(book=self.b_book, name='B现金', initial_balance=Decimal('200'), balance=Decimal('200'))

        self.a_expense_cat = Category.objects.create(book=self.a_book, name='餐饮', type='expense')
        self.a_income_cat = Category.objects.create(book=self.a_book, name='工资', type='income')
        self.b_expense_cat = Category.objects.create(book=self.b_book, name='B餐饮', type='expense')
        self.a_tag = Tag.objects.create(book=self.a_book, name='出差')

        self.client = APIClient()
        self.client.force_authenticate(self.alice)

    def mk_bill(self, book=None, **kw):
        """直接建账单并应用余额（等价于 API 记账流程），便于余额断言。"""
        d = dict(
            book=book or self.a_book, type='expense', amount=Decimal('10'),
            account=self.a_cash, category=self.a_expense_cat,
        )
        d.update(kw)
        bill = Bill.objects.create(**d)
        update_account_balance(bill)
        return bill

    def reset_account(self, account):
        account.refresh_from_db()
        return account.balance


class TransferAuthTests(BillBase):
    def test_transfer_foreign_account_rejected(self):
        # 转入 bob 的账户：无权
        r = self.client.post('/api/accounts/transfer/', {
            'from_account': self.a_cash.id, 'to_account': self.b_cash.id, 'amount': '10',
        }, format='json')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.reset_account(self.a_cash), Decimal('100'))

    def test_transfer_from_foreign_account_rejected(self):
        # 从 bob 的账户转出：无权
        r = self.client.post('/api/accounts/transfer/', {
            'from_account': self.b_cash.id, 'to_account': self.a_cash.id, 'amount': '10',
        }, format='json')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.reset_account(self.b_cash), Decimal('200'))

    def test_transfer_across_books_of_same_user_rejected(self):
        r = self.client.post('/api/accounts/transfer/', {
            'from_account': self.a_cash.id, 'to_account': self.a_other.id, 'amount': '10',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_transfer_same_account_rejected(self):
        r = self.client.post('/api/accounts/transfer/', {
            'from_account': self.a_cash.id, 'to_account': self.a_cash.id, 'amount': '10',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_transfer_success_updates_balance_and_creates_bill(self):
        r = self.client.post('/api/accounts/transfer/', {
            'from_account': self.a_cash.id, 'to_account': self.a_wx.id, 'amount': '10', 'remark': '转账测试',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.reset_account(self.a_cash), Decimal('90'))
        self.assertEqual(self.reset_account(self.a_wx), Decimal('60'))
        bill = Bill.objects.get(book=self.a_book, type='transfer')
        self.assertEqual(bill.account_id, self.a_cash.id)
        self.assertEqual(bill.to_account_id, self.a_wx.id)
        self.assertEqual(bill.amount, Decimal('10'))


class BillCreateValidationTests(BillBase):
    def test_cross_book_account_rejected(self):
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'expense', 'amount': '10',
            'account': self.b_cash.id, 'category': self.a_expense_cat.id, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_cross_book_category_rejected(self):
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'expense', 'amount': '10',
            'account': self.a_cash.id, 'category': self.b_expense_cat.id, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_cross_book_tag_rejected(self):
        bob_tag = Tag.objects.create(book=self.b_book, name='B标签')
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'expense', 'amount': '10',
            'account': self.a_cash.id, 'category': self.a_expense_cat.id, 'tags': [bob_tag.id],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_other_users_book_rejected(self):
        r = self.client.post('/api/bills/', {
            'book': self.b_book.id, 'type': 'expense', 'amount': '10',
            'account': self.b_cash.id, 'category': self.b_expense_cat.id, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 403)

    def test_amount_must_be_positive(self):
        for bad in ('0', '-5'):
            r = self.client.post('/api/bills/', {
                'book': self.a_book.id, 'type': 'expense', 'amount': bad,
                'account': self.a_cash.id, 'category': self.a_expense_cat.id, 'tags': [],
            }, format='json')
            self.assertEqual(r.status_code, 400)

    def test_category_type_must_match_bill_type(self):
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'income', 'amount': '10',
            'account': self.a_cash.id, 'category': self.a_expense_cat.id, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_expense_requires_category(self):
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'expense', 'amount': '10',
            'account': self.a_cash.id, 'category': None, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_transfer_requires_to_account(self):
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'transfer', 'amount': '10',
            'account': self.a_cash.id, 'to_account': None, 'category': None, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_status_is_readonly(self):
        bill = self.mk_bill()
        r = self.client.patch(f'/api/bills/{bill.id}/', {'status': 'deleted'}, format='json')
        self.assertEqual(r.status_code, 200)
        bill.refresh_from_db()
        self.assertEqual(bill.status, 'normal')

    def test_create_success_updates_balance(self):
        r = self.client.post('/api/bills/', {
            'book': self.a_book.id, 'type': 'expense', 'amount': '10',
            'account': self.a_cash.id, 'category': self.a_expense_cat.id, 'tags': [],
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.reset_account(self.a_cash), Decimal('90'))

    def test_update_reverts_then_applies_balance(self):
        self.mk_bill(amount=Decimal('10'))
        bill = Bill.objects.get()
        self.assertEqual(self.reset_account(self.a_cash), Decimal('90'))
        r = self.client.patch(f'/api/bills/{bill.id}/', {'amount': '30'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.reset_account(self.a_cash), Decimal('70'))


class BatchActionTests(BillBase):
    def setUp(self):
        super().setUp()
        self.bills = [self.mk_bill(amount=Decimal('10')) for _ in range(3)]
        self.bobs_bill = Bill.objects.create(
            book=self.b_book, type='expense', amount=Decimal('5'),
            account=self.b_cash, category=self.b_expense_cat,
        )

    def test_batch_delete_count_is_correct(self):
        ids = [b.id for b in self.bills]
        r = self.client.post('/api/bills/batch_delete/', {'ids': ids}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['deleted_count'], 3)
        self.assertEqual(Bill.objects.filter(status='normal', id__in=ids).count(), 0)
        self.assertEqual(Bill.objects.filter(status='deleted', id__in=ids).count(), 3)
        # 余额已回滚：现金账户余额回到初始 100
        self.assertEqual(self.reset_account(self.a_cash), Decimal('100'))

    def test_batch_delete_ignores_foreign_bills(self):
        ids = [b.id for b in self.bills] + [self.bobs_bill.id]
        r = self.client.post('/api/bills/batch_delete/', {'ids': ids}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['deleted_count'], 3)
        self.bobs_bill.refresh_from_db()
        self.assertEqual(self.bobs_bill.status, 'normal')
        self.assertEqual(self.reset_account(self.b_cash), Decimal('200'))

    def test_batch_update_category_rejects_foreign_category(self):
        r = self.client.post('/api/bills/batch_update_category/', {
            'ids': [b.id for b in self.bills], 'category_id': self.b_expense_cat.id,
        }, format='json')
        self.assertEqual(r.status_code, 404)
        for b in self.bills:
            b.refresh_from_db()
            self.assertEqual(b.category_id, self.a_expense_cat.id)

    def test_batch_update_category_only_matching_type(self):
        income_bill = self.mk_bill(type='income', amount=Decimal('20'), category=self.a_income_cat)
        r = self.client.post('/api/bills/batch_update_category/', {
            'ids': [b.id for b in self.bills] + [income_bill.id],
            'category_id': self.a_expense_cat.id,
        }, format='json')
        self.assertEqual(r.status_code, 200)
        # 只有 3 条支出账单被更新，收入账单不动
        self.assertEqual(r.data['updated_count'], 3)
        income_bill.refresh_from_db()
        self.assertEqual(income_bill.category_id, self.a_income_cat.id)


class RestorePermanentDeleteTests(BillBase):
    def setUp(self):
        super().setUp()
        self.bill = self.mk_bill(amount=Decimal('10'))
        self.bobs_deleted = Bill.objects.create(
            book=self.b_book, type='expense', amount=Decimal('5'),
            account=self.b_cash, category=self.b_expense_cat, status='deleted',
        )

    def test_restore_foreign_bill_rejected(self):
        r = self.client.post(f'/api/bills/{self.bobs_deleted.id}/restore/')
        self.assertEqual(r.status_code, 404)

    def test_restore_own_bill_reapplies_balance(self):
        # 先软删自己的账单，余额回滚
        r = self.client.delete(f'/api/bills/{self.bill.id}/')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.reset_account(self.a_cash), Decimal('100'))
        # 恢复后余额重新入账
        r = self.client.post(f'/api/bills/{self.bill.id}/restore/')
        self.assertEqual(r.status_code, 200)
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, 'normal')
        self.assertEqual(self.reset_account(self.a_cash), Decimal('90'))

    def test_permanent_delete_foreign_bill_rejected(self):
        r = self.client.post(f'/api/bills/{self.bobs_deleted.id}/permanent_delete/')
        self.assertEqual(r.status_code, 404)
        self.assertTrue(Bill.objects.filter(pk=self.bobs_deleted.id).exists())

    def test_permanent_delete_own_bill(self):
        self.client.delete(f'/api/bills/{self.bill.id}/')
        r = self.client.post(f'/api/bills/{self.bill.id}/permanent_delete/')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Bill.objects.filter(pk=self.bill.id).exists())


class ListPaginationTests(BillBase):
    def test_list_is_owner_scoped(self):
        self.mk_bill()
        Bill.objects.create(
            book=self.b_book, type='expense', amount=Decimal('5'),
            account=self.b_cash, category=self.b_expense_cat,
        )
        r = self.client.get('/api/bills/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)

    def test_list_returns_paginated_envelope(self):
        for i in range(25):
            self.mk_bill(amount=Decimal(str(i + 1)))
        r = self.client.get('/api/bills/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 25)
        self.assertEqual(len(r.data['results']), 20)
        self.assertIsNotNone(r.data['next'])

    def test_page_and_size_params(self):
        for i in range(25):
            self.mk_bill(amount=Decimal(str(i + 1)))
        r = self.client.get('/api/bills/', {'page': 2, 'size': 10})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data['results']), 10)

    def test_recycle_bin_scoped_by_book(self):
        self.client.delete(f"/api/bills/{self.mk_bill().id}/")
        r = self.client.get('/api/bills/recycle_bin/', {'book': self.a_book.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        r2 = self.client.get('/api/bills/recycle_bin/', {'book': self.a_book2.id})
        self.assertEqual(r2.data['count'], 0)

    def test_bill_edit_rejects_cross_book_account_move(self):
        """编辑账单时把账户换成另一账本的账户 → 400"""
        bill = self.mk_bill()
        r = self.client.patch(f'/api/bills/{bill.id}/', {'account': self.a_other.id}, format='json')
        self.assertEqual(r.status_code, 400)
