from django.contrib import admin
from django.db import transaction

from .models import Book, Account, Category, Tag, Bill
from .models import update_account_balance, revert_account_balance, recompute_balance


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'budget', 'is_default', 'is_archived', 'created_at')
    list_filter = ('is_default', 'is_archived', 'owner')
    search_fields = ('name', 'remark')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'book', 'balance', 'is_active', 'created_at')
    list_filter = ('type', 'is_active', 'book')
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            obj.save()
            # 改初始余额后，余额按流水重算，保持对账一致
            recompute_balance(obj)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'book', 'budget', 'is_active')
    list_filter = ('type', 'is_active', 'book')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'book', 'created_at')
    list_filter = ('book',)
    search_fields = ('name',)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'occurred_at', 'category', 'account', 'to_account', 'book', 'status')
    list_filter = ('type', 'status', 'book')
    search_fields = ('remark',)
    date_hierarchy = 'occurred_at'
    autocomplete_fields = ['category', 'account', 'to_account', 'tags']

    def save_model(self, request, obj, form, change):
        # 后台增改账单也要同步账户余额，revert+save+入账 全有或全无
        with transaction.atomic():
            if change:
                old = Bill.objects.get(pk=obj.pk)
                revert_account_balance(old)
            obj.save()
            update_account_balance(obj)

    def delete_model(self, request, obj):
        with transaction.atomic():
            revert_account_balance(obj)
            obj.delete()

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for b in queryset:
                revert_account_balance(b)
            queryset.delete()
