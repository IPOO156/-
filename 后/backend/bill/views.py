from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import (
    Book, Account, Category, Tag, Bill,
    update_account_balance, revert_account_balance, recompute_balance,
)
from .pagination import BillPagination
from .serializers import (
    BookSerializer, AccountSerializer, CategorySerializer,
    TagSerializer, BillSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_auth(request):
    return Response({
        'message': 'Token 认证成功',
        'user': request.user.username,
        'user_id': request.user.id,
        'is_staff': request.user.is_staff,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def test_public(request):
    return Response({
        'message': '这是公开接口，无需 Token 即可访问',
    })


def _lock_accounts(account_ids):
    """按 id 升序加锁账户行（避免死锁），返回 {id: Account}。须在 transaction.atomic() 内调用。"""
    ids = {i for i in account_ids if i}
    if not ids:
        return {}
    locked = Account.objects.filter(id__in=ids).select_for_update().order_by('id')
    return {a.id: a for a in locked}


def _attach_locked(bill, accounts):
    """把已加锁的账户实例挂回 bill，保证余额读写基于锁内最新值。"""
    bill.account = accounts[bill.account_id]
    if bill.to_account_id and bill.to_account_id != bill.account_id:
        bill.to_account = accounts[bill.to_account_id]


def _apply_balance(bill, accounts=None):
    """事务内按账单类型调整余额；未传入 accounts 时先加锁再调整。"""
    if accounts is None:
        accounts = _lock_accounts([bill.account_id, bill.to_account_id])
    _attach_locked(bill, accounts)
    update_account_balance(bill)


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer

    def get_queryset(self):
        queryset = Book.objects.filter(owner=self.request.user)
        archived = self.request.query_params.get('archived')
        if archived is not None:
            is_archived = archived.lower() in ('1', 'true', 'yes')
            queryset = queryset.filter(is_archived=is_archived)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        book = self.get_object()
        book.is_archived = True
        book.save()
        return Response(self.get_serializer(book).data)

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        book = self.get_object()
        book.is_archived = False
        book.save()
        return Response(self.get_serializer(book).data)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        Book.objects.filter(owner=request.user).update(is_default=False)
        book = self.get_object()
        book.is_default = True
        book.save()
        return Response(self.get_serializer(book).data)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def perform_create(self, serializer):
        book = serializer.validated_data.get('book')
        if book is not None and book.owner_id != self.request.user.id:
            raise PermissionDenied('无权在他人账本下操作')
        instance = serializer.save()
        if instance.initial_balance and instance.balance == 0:
            instance.balance = instance.initial_balance
            instance.save()

    def perform_update(self, serializer):
        book = serializer.validated_data.get('book')
        if book is not None and book.owner_id != self.request.user.id:
            raise PermissionDenied('无权把账户移到他人账本下')
        account = serializer.save()
        recompute_balance(account)

    def get_queryset(self):
        queryset = Account.objects.filter(book__owner=self.request.user)
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        active = self.request.query_params.get('active')
        if active is not None:
            is_active = active.lower() in ('1', 'true', 'yes')
            queryset = queryset.filter(is_active=is_active)
        return queryset

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        account = self.get_object()
        account.is_active = False
        account.save()
        return Response(self.get_serializer(account).data)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        account = self.get_object()
        account.is_active = True
        account.save()
        return Response(self.get_serializer(account).data)

    @action(detail=False, methods=['post'])
    def transfer(self, request):
        from_account_id = request.data.get('from_account')
        to_account_id = request.data.get('to_account')
        amount = Decimal(str(request.data.get('amount', 0)))
        if not from_account_id or not to_account_id or amount <= 0:
            return Response({'detail': '参数错误：需提供 from_account、to_account 和 amount>0'}, status=status.HTTP_400_BAD_REQUEST)
        if from_account_id == to_account_id:
            return Response({'detail': '转出和转入账户不能相同'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            accounts = _lock_accounts([from_account_id, to_account_id])
            from_acc = accounts.get(from_account_id)
            to_acc = accounts.get(to_account_id)
            # 归属校验：任一账户非当前用户所有 → 404（不暴露存在性）
            if not from_acc or not to_acc:
                return Response({'detail': '账户不存在'}, status=status.HTTP_404_NOT_FOUND)
            if from_acc.book.owner_id != request.user.id or to_acc.book.owner_id != request.user.id:
                return Response({'detail': '账户不存在'}, status=status.HTTP_404_NOT_FOUND)
            if from_acc.book_id != to_acc.book_id:
                return Response({'detail': '转出与转入账户必须属于同一账本'}, status=status.HTTP_400_BAD_REQUEST)
            from_acc.balance -= amount
            to_acc.balance += amount
            from_acc.save(update_fields=['balance'])
            to_acc.save(update_fields=['balance'])
            bill = Bill.objects.create(
                book=from_acc.book,
                type='transfer',
                amount=amount,
                account=from_acc,
                to_account=to_acc,
                remark=request.data.get('remark', '账户转账'),
            )
        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.filter(book__owner=self.request.user)
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        type = self.request.query_params.get('type')
        if type:
            queryset = queryset.filter(type=type)
        active = self.request.query_params.get('active')
        if active is not None:
            is_active = active.lower() in ('1', 'true', 'yes')
            queryset = queryset.filter(is_active=is_active)
        return queryset

    def perform_create(self, serializer):
        book = serializer.validated_data.get('book')
        if book is not None and book.owner_id != self.request.user.id:
            raise PermissionDenied('无权在他人账本下操作')
        serializer.save()

    def perform_update(self, serializer):
        book = serializer.validated_data.get('book')
        if book is not None and book.owner_id != self.request.user.id:
            raise PermissionDenied('无权把分类移到他人账本下')
        serializer.save()

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        cat = self.get_object()
        cat.is_active = False
        cat.save()
        return Response(self.get_serializer(cat).data)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        cat = self.get_object()
        cat.is_active = True
        cat.save()
        return Response(self.get_serializer(cat).data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.filter(book__owner=self.request.user)
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        return queryset

    def perform_create(self, serializer):
        book = serializer.validated_data.get('book')
        if book is not None and book.owner_id != self.request.user.id:
            raise PermissionDenied('无权在他人账本下操作')
        serializer.save()

    def perform_update(self, serializer):
        book = serializer.validated_data.get('book')
        if book is not None and book.owner_id != self.request.user.id:
            raise PermissionDenied('无权把标签移到他人账本下')
        serializer.save()


class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.filter(status='normal')
    serializer_class = BillSerializer
    pagination_class = BillPagination

    def get_queryset(self):
        queryset = Bill.objects.filter(status='normal', book__owner=self.request.user)
        params = self.request.query_params

        book_id = params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        type = params.get('type')
        if type:
            queryset = queryset.filter(type=type)
        category_id = params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        account_id = params.get('account')
        if account_id:
            queryset = queryset.filter(Q(account_id=account_id) | Q(to_account_id=account_id))
        tag_id = params.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        start_date = params.get('start_date')
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(occurred_at__gte=start_dt)
        end_date = params.get('end_date')
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(occurred_at__lt=end_dt)
        keyword = params.get('keyword')
        if keyword:
            queryset = queryset.filter(remark__icontains=keyword)
        recurring = params.get('recurring')
        if recurring is not None:
            is_recurring = recurring.lower() in ('1', 'true', 'yes')
            queryset = queryset.filter(is_recurring=is_recurring)
        ordering = params.get('ordering')
        if ordering:
            allowed = {'occurred_at', '-occurred_at', 'amount', '-amount', 'created_at', '-created_at'}
            if ordering in allowed:
                queryset = queryset.order_by(ordering)
        # 关联预取：避免列表/回收站序列化时的 N+1 查询
        queryset = queryset.select_related('category', 'account', 'to_account', 'book').prefetch_related('tags')
        return queryset.distinct()

    def perform_create(self, serializer):
        # 归属/跨账本校验在 BillSerializer.validate() 中完成
        with transaction.atomic():
            bill = serializer.save()
            _apply_balance(bill)

    def perform_update(self, serializer):
        with transaction.atomic():
            bill = self.get_object()  # get_queryset 已按 owner 过滤
            old_account_id = bill.account_id
            old_to_account_id = bill.to_account_id
            new_account = serializer.validated_data.get('account')
            new_to_account = serializer.validated_data.get('to_account')
            new_account_id = new_account.id if new_account is not None else old_account_id
            new_to_account_id = new_to_account.id if new_to_account is not None else old_to_account_id
            accounts = _lock_accounts([old_account_id, old_to_account_id, new_account_id, new_to_account_id])
            _attach_locked(bill, accounts)
            revert_account_balance(bill)
            new_bill = serializer.save()
            _apply_balance(new_bill, accounts)

    def perform_destroy(self, instance):
        with transaction.atomic():
            accounts = _lock_accounts([instance.account_id, instance.to_account_id])
            _attach_locked(instance, accounts)
            revert_account_balance(instance)
            instance.status = 'deleted'
            instance.save(update_fields=['status'])

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': '请提供 ids 数组'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            bills = list(Bill.objects.filter(
                id__in=ids, status='normal', book__owner=request.user,
            ).select_related('account', 'to_account').order_by('id'))
            deleted_count = len(bills)  # 先物化计数：软删后按 status='normal' 查不到，原实现返回 0
            acc_ids = [a for b in bills for a in (b.account_id, b.to_account_id)]
            accounts = _lock_accounts(acc_ids)
            for b in bills:
                _attach_locked(b, accounts)
                revert_account_balance(b)
                b.status = 'deleted'
                b.save(update_fields=['status'])
        return Response({'deleted_count': deleted_count})

    @action(detail=False, methods=['post'])
    def batch_update_category(self, request):
        ids = request.data.get('ids', [])
        category_id = request.data.get('category_id')
        if not ids or not category_id:
            return Response({'detail': '请提供 ids 和 category_id'}, status=status.HTTP_400_BAD_REQUEST)
        cat = Category.objects.filter(pk=category_id, book__owner=request.user).first()
        if not cat:
            return Response({'detail': '分类不存在或无权操作'}, status=status.HTTP_404_NOT_FOUND)
        # 仅更新当前用户、同账本且类型匹配的账单；不匹配的不计入
        qs = Bill.objects.filter(
            id__in=ids, status='normal', book__owner=request.user,
            book_id=cat.book_id, type=cat.type,
        )
        updated = qs.update(category_id=cat.id)
        return Response({'updated_count': updated})

    @action(detail=False, methods=['get'])
    def recycle_bin(self, request):
        queryset = Bill.objects.filter(status='deleted', book__owner=request.user)
        book_id = request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        queryset = queryset.select_related('category', 'account', 'to_account', 'book').prefetch_related('tags')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        with transaction.atomic():
            # 默认 queryset 只含 status='normal'，这里按 owner 限定显式取软删记录
            bill = get_object_or_404(Bill.objects.filter(status='deleted', book__owner=request.user), pk=pk)
            bill.status = 'normal'
            bill.save(update_fields=['status'])
            _apply_balance(bill)
        return Response(self.get_serializer(bill).data)

    @action(detail=True, methods=['post'])
    def permanent_delete(self, request, pk=None):
        # 余额已在软删时回滚，这里只需删除记录
        bill = get_object_or_404(Bill.objects.filter(status='deleted', book__owner=request.user), pk=pk)
        bill.delete()
        return Response({'detail': '已彻底删除'})


def _get_date_range(time_range, start_date, end_date):
    now = timezone.localtime()
    if time_range == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif time_range == 'week':
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif time_range == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1)
    elif time_range == 'year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
    elif time_range == 'custom' and start_date and end_date:
        start = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        end = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d')) + timedelta(days=1)
    else:
        start = None
        end = None
    return start, end


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_overview(request):
    book_id = request.query_params.get('book')
    time_range = request.query_params.get('range', 'month')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    qs = Bill.objects.filter(status='normal', book__owner=request.user)
    if book_id:
        qs = qs.filter(book_id=book_id)
    start, end = _get_date_range(time_range, start_date, end_date)
    if start and end:
        qs = qs.filter(occurred_at__gte=start, occurred_at__lt=end)

    expense_total = qs.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
    income_total = qs.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
    balance = income_total - expense_total

    book_qs = Book.objects.filter(owner=request.user, id=book_id) if book_id else Book.objects.filter(owner=request.user)
    total_budget = book_qs.aggregate(s=Sum('budget'))['s'] or 0
    budget_used = expense_total
    budget_remaining = max(total_budget - budget_used, 0)
    budget_percent = float(budget_used / total_budget * 100) if total_budget > 0 else 0

    account_qs = Account.objects.filter(book__owner=request.user, book_id=book_id) if book_id else Account.objects.filter(book__owner=request.user)
    total_account_balance = account_qs.aggregate(s=Sum('balance'))['s'] or 0
    account_count = account_qs.filter(is_active=True).count()

    bill_count = qs.count()

    return Response({
        'expense_total': expense_total,
        'income_total': income_total,
        'balance': balance,
        'total_budget': total_budget,
        'budget_used': budget_used,
        'budget_remaining': budget_remaining,
        'budget_percent': round(budget_percent, 2),
        'total_account_balance': total_account_balance,
        'account_count': account_count,
        'bill_count': bill_count,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_pie(request):
    book_id = request.query_params.get('book')
    time_range = request.query_params.get('range', 'month')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    type = request.query_params.get('type', 'expense')

    qs = Bill.objects.filter(status='normal', type=type, book__owner=request.user)
    if book_id:
        qs = qs.filter(book_id=book_id)
    start, end = _get_date_range(time_range, start_date, end_date)
    if start and end:
        qs = qs.filter(occurred_at__gte=start, occurred_at__lt=end)

    data = qs.values('category_id', 'category__name', 'category__color').annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('-total')

    total = sum(d['total'] or 0 for d in data) or 1
    result = []
    for item in data:
        result.append({
            'category_id': item['category_id'],
            'category_name': item['category__name'],
            'color': item['category__color'],
            'total': item['total'] or 0,
            'count': item['count'],
            'percent': round(float((item['total'] or 0) / total * 100), 2),
        })
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_trend(request):
    book_id = request.query_params.get('book')
    time_range = request.query_params.get('range', 'month')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    granularity = request.query_params.get('granularity', 'day')

    qs = Bill.objects.filter(status='normal', book__owner=request.user)
    if book_id:
        qs = qs.filter(book_id=book_id)
    start, end = _get_date_range(time_range, start_date, end_date)
    if not (start and end):
        return Response([])

    result = {}
    current = start
    while current < end:
        if granularity == 'day':
            key = current.strftime('%Y-%m-%d')
            next = current + timedelta(days=1)
        elif granularity == 'month':
            key = current.strftime('%Y-%m')
            next_month = current.replace(day=28) + timedelta(days=4)
            next = next_month.replace(day=1)
        else:
            key = current.strftime('%Y-%m-%d')
            next = current + timedelta(days=1)
        result[key] = {'date': key, 'expense': Decimal(0), 'income': Decimal(0)}
        current = next

    day_qs = qs.filter(occurred_at__gte=start, occurred_at__lt=end)
    if granularity == 'day':
        for bill in day_qs:
            key = timezone.localtime(bill.occurred_at).strftime('%Y-%m-%d')
            if key in result:
                if bill.type == 'expense':
                    result[key]['expense'] += bill.amount
                elif bill.type == 'income':
                    result[key]['income'] += bill.amount
    else:
        for bill in day_qs:
            key = timezone.localtime(bill.occurred_at).strftime('%Y-%m')
            if key in result:
                if bill.type == 'expense':
                    result[key]['expense'] += bill.amount
                elif bill.type == 'income':
                    result[key]['income'] += bill.amount

    return Response(sorted(result.values(), key=lambda x: x['date']))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_accounts(request):
    book_id = request.query_params.get('book')
    qs = Account.objects.filter(book__owner=request.user)
    if book_id:
        qs = qs.filter(book_id=book_id)

    result = qs.values('id', 'name', 'type', 'balance', 'is_active').annotate(
        out_count=Count('out_bills', filter=Q(out_bills__status='normal')),
        in_count=Count('in_bills', filter=Q(in_bills__status='normal')),
    ).order_by('-balance')
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_budget(request):
    book_id = request.query_params.get('book')
    now = timezone.localtime()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month.replace(day=1)

    cat_qs = Category.objects.filter(type='expense', budget__gt=0, book__owner=request.user)
    if book_id:
        cat_qs = cat_qs.filter(book_id=book_id)

    bill_qs = Bill.objects.filter(
        status='normal', type='expense',
        occurred_at__gte=start, occurred_at__lt=end,
        book__owner=request.user,
    )
    if book_id:
        bill_qs = bill_qs.filter(book_id=book_id)

    # 一次分组聚合取代「按分类循环查询」（N+1 → 2 条查询）
    usage_rows = (
        bill_qs.filter(category_id__isnull=False)
        .values('category_id')
        .annotate(used=Sum('amount'))
    )
    usage_map = {r['category_id']: (r['used'] or Decimal(0)) for r in usage_rows}

    result = []
    for cat in cat_qs:
        used = usage_map.get(cat.id, Decimal(0))
        percent = float(used / cat.budget * 100) if cat.budget > 0 else 0
        result.append({
            'category_id': cat.id,
            'category_name': cat.name,
            'color': cat.color,
            'budget': cat.budget,
            'used': used,
            'remaining': max(cat.budget - used, Decimal(0)),
            'percent': round(percent, 2),
            'over_budget': used > cat.budget,
        })

    book = Book.objects.filter(owner=request.user, id=book_id).first() if book_id else Book.objects.filter(owner=request.user, is_default=True).first()
    book_budget = book.budget if book else Decimal(0)
    # 账本总预算进度应统计当月全部支出，而非仅统计设了预算的分类
    book_used = bill_qs.aggregate(s=Sum('amount'))['s'] or Decimal(0)
    book_percent = float(book_used / book_budget * 100) if book_budget > 0 else 0
    return Response({
        'book_budget': book_budget,
        'book_used': book_used,
        'book_remaining': max(book_budget - book_used, Decimal(0)),
        'book_percent': round(book_percent, 2),
        'book_over_budget': book_used > book_budget,
        'categories': result,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics_tags(request):
    book_id = request.query_params.get('book')
    time_range = request.query_params.get('range', 'month')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    # 标签统计聚焦真实收支：排除转账（无收支方向，混入会导致金额难对账）
    qs = Bill.objects.filter(status='normal', book__owner=request.user).exclude(type='transfer')
    if book_id:
        qs = qs.filter(book_id=book_id)
    start, end = _get_date_range(time_range, start_date, end_date)
    if start and end:
        qs = qs.filter(occurred_at__gte=start, occurred_at__lt=end)

    # total 语义：带该标签账单的金额之和。同一账单打了多个标签时，会完整计入每个标签（标签非互斥），
    # 故「各标签金额之和」可大于「账单总支出」，属预期现象。count 用 DISTINCT 去重，反映去重笔数。
    data = qs.filter(tags__isnull=False).values('tags__id', 'tags__name', 'tags__color').annotate(
        total=Sum('amount'),
        count=Count('id', distinct=True),
    ).order_by('-total')

    result = []
    for item in data:
        result.append({
            'tag_id': item['tags__id'],
            'tag_name': item['tags__name'],
            'color': item['tags__color'],
            'total': item['total'] or 0,
            'count': item['count'],
        })
    return Response(result)