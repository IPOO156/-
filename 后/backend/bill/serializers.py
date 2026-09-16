from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import Book, Account, Category, Tag, Bill


class BookSerializer(serializers.ModelSerializer):
    account_count = serializers.SerializerMethodField()
    bill_count = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'
        # owner 只读：归属只能由 perform_create 显式赋值，禁止客户端转移所有权
        read_only_fields = ['created_at', 'updated_at', 'owner']

    def get_account_count(self, obj):
        return obj.accounts.count()

    def get_bill_count(self, obj):
        return obj.bills.filter(status='normal').count()


class AccountSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'balance']


class CategorySerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    bill_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_bill_count(self, obj):
        return obj.bills.filter(status='normal').count()


class BillSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recurring_type_display = serializers.CharField(source='get_recurring_type_display', read_only=True)
    tag_names = serializers.SerializerMethodField()
    account_name = serializers.CharField(source='account.name', read_only=True)
    to_account_name = serializers.CharField(source='to_account.name', read_only=True, default=None)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    category_type = serializers.CharField(source='category.type', read_only=True, default=None)

    class Meta:
        model = Bill
        fields = '__all__'
        # status 只读：软删/恢复只能走专用接口，避免绕过余额回滚逻辑
        read_only_fields = ['created_at', 'updated_at', 'status']

    def get_tag_names(self, obj):
        return list(obj.tags.values_list('name', flat=True))

    def validate(self, attrs):
        """记账/改账的核心校验：归属 + 类型一致性 + 跨账本引用（PATCH 时缺失字段回退实例旧值）"""
        request = self.context.get('request')
        instance = self.instance

        def v(field, default=None):
            if field in attrs:
                return attrs[field]
            if instance is not None:
                return getattr(instance, field, default)
            return default

        book = v('book')
        btype = v('type')
        amount = v('amount')
        account = v('account')
        to_account = v('to_account')
        category = v('category')

        if book is None:
            raise serializers.ValidationError({'book': '请选择账本'})
        if request is not None and book.owner_id != request.user.id:
            raise PermissionDenied('无权在他人账本下记账')
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({'amount': '金额必须大于 0'})

        # 类型 ↔ 分类一致性
        if btype in ('expense', 'income'):
            if category is None:
                raise serializers.ValidationError({'category': '支出/收入账单必须选择分类'})
            if category.type != btype:
                raise serializers.ValidationError({'category': f'{btype} 账单只能选择 {btype} 分类'})
        elif btype == 'transfer':
            if category is not None:
                raise serializers.ValidationError({'category': '转账账单不能选择分类'})
            if to_account is None:
                raise serializers.ValidationError({'to_account': '转账账单必须选择转入账户'})
            if account is not None and to_account is not None and account.id == to_account.id:
                raise serializers.ValidationError({'to_account': '转入账户不能与转出账户相同'})
        else:
            raise serializers.ValidationError({'type': '无效的账单类型'})

        # 跨账本引用校验：account / to_account / category / tags 必须属于同一账本
        refs = {'account': account}
        if to_account is not None:
            refs['to_account'] = to_account
        if category is not None:
            refs['category'] = category
        for field, obj in refs.items():
            if obj is not None and obj.book_id != book.id:
                raise serializers.ValidationError({field: '引用对象不属于当前账本'})

        tag_list = attrs.get('tags')
        if tag_list is None and instance is not None:
            tag_list = list(instance.tags.all())
        for t in tag_list or []:
            if t.book_id != book.id:
                raise serializers.ValidationError({'tags': '标签不属于当前账本'})

        return attrs