"""账单列表分页：只对 Bill 相关接口启用，其余列表保持纯数组返回"""

from rest_framework.pagination import PageNumberPagination


class BillPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'
    max_page_size = 100
