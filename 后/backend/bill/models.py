from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.models import User


class Book(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books', verbose_name='所属用户', null=True)
    name = models.CharField(max_length=100, verbose_name='账本名称')
    remark = models.CharField(max_length=500, blank=True, verbose_name='备注')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='月度预算')
    cover = models.CharField(max_length=200, blank=True, verbose_name='账本封面')
    is_archived = models.BooleanField(default=False, verbose_name='是否归档')
    is_default = models.BooleanField(default=False, verbose_name='是否默认账本')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'book'
        verbose_name = '账本'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Account(models.Model):
    ACCOUNT_TYPE = (
        ('cash', '现金'),
        ('wechat', '微信'),
        ('alipay', '支付宝'),
        ('bank_card', '银行卡'),
        ('credit_card', '信用卡'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='accounts', verbose_name='所属账本')
    name = models.CharField(max_length=100, verbose_name='账户名称')
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPE, default='cash', verbose_name='账户类型')
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='初始余额')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='当前余额')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'account'
        verbose_name = '账户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'


class Category(models.Model):
    CATEGORY_TYPE = (
        ('expense', '支出'),
        ('income', '收入'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='categories', verbose_name='所属账本')
    name = models.CharField(max_length=100, verbose_name='分类名称')
    type = models.CharField(max_length=20, choices=CATEGORY_TYPE, default='expense', verbose_name='分类类型')
    icon = models.CharField(max_length=100, blank=True, verbose_name='分类图标')
    color = models.CharField(max_length=20, blank=True, verbose_name='分类颜色')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_default = models.BooleanField(default=False, verbose_name='是否系统默认')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='分类月度预算')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'category'
        verbose_name = '分类'
        verbose_name_plural = verbose_name
        ordering = ['type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'


class Tag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='tags', verbose_name='所属账本')
    name = models.CharField(max_length=50, verbose_name='标签名称')
    color = models.CharField(max_length=20, blank=True, verbose_name='标签颜色')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'tag'
        verbose_name = '标签'
        verbose_name_plural = verbose_name
        unique_together = ('book', 'name')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Bill(models.Model):
    BILL_TYPE = (
        ('expense', '支出'),
        ('income', '收入'),
        ('transfer', '转账'),
    )

    BILL_STATUS = (
        ('normal', '正常'),
        ('deleted', '已删除'),
    )

    RECURRING_TYPE = (
        ('none', '无'),
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('yearly', '每年'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bills', verbose_name='所属账本')
    type = models.CharField(max_length=20, choices=BILL_TYPE, default='expense', verbose_name='账单类型')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='金额')
    occurred_at = models.DateTimeField(default=timezone.now, verbose_name='发生时间')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='bills', verbose_name='分类')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='out_bills', verbose_name='账户（转出）')
    to_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name='in_bills', verbose_name='转入账户（转账）')
    remark = models.CharField(max_length=500, blank=True, verbose_name='备注')
    receipt_image = models.CharField(max_length=500, blank=True, verbose_name='凭证图片')
    tags = models.ManyToManyField(Tag, blank=True, related_name='bills', verbose_name='标签')
    status = models.CharField(max_length=20, choices=BILL_STATUS, default='normal', verbose_name='状态')
    is_recurring = models.BooleanField(default=False, verbose_name='是否周期账单')
    recurring_type = models.CharField(max_length=20, choices=RECURRING_TYPE, default='none', verbose_name='周期类型')
    recurring_next_at = models.DateTimeField(null=True, blank=True, verbose_name='下次自动入账时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'bill'
        verbose_name = '账单'
        verbose_name_plural = verbose_name
        ordering = ['-occurred_at', '-id']
        indexes = [
            # 列表筛选：账本 + 状态 + 时间
            models.Index(fields=['book', 'status', 'occurred_at'], name='bill_book_status_time_idx'),
            # 统计分组：账本 + 类型 + 时间
            models.Index(fields=['book', 'type', 'occurred_at'], name='bill_book_type_time_idx'),
            models.Index(fields=['category'], name='bill_category_idx'),
            models.Index(fields=['account'], name='bill_account_idx'),
            models.Index(fields=['to_account'], name='bill_to_account_idx'),
        ]

    def __str__(self):
        return f'{self.get_type_display()} - {self.amount} ({self.occurred_at.strftime("%Y-%m-%d")})'

def update_account_balance(bill):
    """记账后按类型调整账户余额（API 与后台共用）"""
    amount = bill.amount
    if bill.type == 'expense':
        bill.account.balance -= amount
        bill.account.save(update_fields=['balance'])
    elif bill.type == 'income':
        bill.account.balance += amount
        bill.account.save(update_fields=['balance'])
    elif bill.type == 'transfer':
        bill.account.balance -= amount
        bill.account.save(update_fields=['balance'])
        if bill.to_account:
            bill.to_account.balance += amount
            bill.to_account.save(update_fields=['balance'])


def revert_account_balance(bill):
    """撤销账单对余额的影响（改/删前调用）"""
    amount = bill.amount
    if bill.type == 'expense':
        bill.account.balance += amount
        bill.account.save(update_fields=['balance'])
    elif bill.type == 'income':
        bill.account.balance -= amount
        bill.account.save(update_fields=['balance'])
    elif bill.type == 'transfer':
        bill.account.balance += amount
        bill.account.save(update_fields=['balance'])
        if bill.to_account:
            bill.to_account.balance -= amount
            bill.to_account.save(update_fields=['balance'])


def recompute_balance(account):
    """按 初始余额 + 收入 - 支出 - 转出 + 转入 重算账户余额（对账）"""
    qs = Bill.objects.filter(account=account, status='normal')
    income = qs.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
    expense = qs.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
    out = qs.filter(type='transfer').aggregate(s=Sum('amount'))['s'] or 0
    inn = Bill.objects.filter(status='normal', type='transfer', to_account=account).aggregate(s=Sum('amount'))['s'] or 0
    account.balance = account.initial_balance + income - expense - out + inn
    account.save(update_fields=['balance'])
