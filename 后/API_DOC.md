# 个人记账系统 - 后端 API 文档

> Base URL（本地）：`http://127.0.0.1:8000/api`
> Base URL（公网）：`https://squatting-agent-creed.ngrok-free.dev/api`
>
> 所有私有接口需要 Header：`Authorization: Token 3HoA0NH65QAwgzGt3acVF2Ny75v_hMkrLK4xCvXyspqpdHdX`
> Token 获取：`POST /api/token/` body: `username=admin&password=admin123`

---

## 0. 认证与测试

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| `POST` | `/api/token/` | 公开 | 用户名密码换取 Token |
| `GET` | `/api/test/public/` | 公开 | 公开测试接口 |
| `GET` | `/api/test/auth/` | Token | 认证测试，返回用户信息 |

---

## 1. 账本 Book

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/books/` | 账本列表，query：`?archived=true` 只看归档 |
| `POST` | `/api/books/` | 新建账本 |
| `GET` | `/api/books/{id}/` | 账本详情 |
| `PUT` / `PATCH` | `/api/books/{id}/` | 编辑账本 |
| `DELETE` | `/api/books/{id}/` | 删除账本 |
| `POST` | `/api/books/{id}/archive/` | 归档账本 |
| `POST` | `/api/books/{id}/unarchive/` | 取消归档 |
| `POST` | `/api/books/{id}/set_default/` | 设为默认账本 |

### Book 字段

```json
{
  "id": 1,
  "name": "日常账本",
  "remark": "日常花销",
  "budget": 3000,
  "cover": "",
  "is_archived": false,
  "is_default": true,
  "account_count": 3,
  "bill_count": 2,
  "created_at": "2026-08-12T00:00:00Z",
  "updated_at": "2026-08-12T00:00:00Z"
}
```

---

## 2. 账户 Account

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/accounts/` | 账户列表，query：`?book=1&active=true` |
| `POST` | `/api/accounts/` | 新建账户（创建时 balance 自动 = initial_balance） |
| `GET` | `/api/accounts/{id}/` | 账户详情 |
| `PUT` / `PATCH` | `/api/accounts/{id}/` | 编辑账户 |
| `DELETE` | `/api/accounts/{id}/` | 删除账户 |
| `POST` | `/api/accounts/{id}/disable/` | 停用账户 |
| `POST` | `/api/accounts/{id}/enable/` | 启用账户 |
| `POST` | `/api/accounts/transfer/` | 账户互转 |

### 账户类型 Account.type

| 值 | 显示 |
|----|------|
| `cash` | 现金 |
| `wechat` | 微信 |
| `alipay` | 支付宝 |
| `bank_card` | 银行卡 |
| `credit_card` | 信用卡 |

### 账户互转 POST `/api/accounts/transfer/`

```json
{
  "from_account": 1,
  "to_account": 2,
  "amount": 500,
  "remark": "微信充值到支付宝"
}
```

### Account 字段

```json
{
  "id": 1,
  "book": 1,
  "name": "微信钱包",
  "type": "wechat",
  "type_display": "微信",
  "initial_balance": 1500,
  "balance": 1467.5,
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 3. 分类 Category

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/categories/` | 分类列表，query：`?book=1&type=expense&active=true` |
| `POST` | `/api/categories/` | 新建分类 |
| `GET` | `/api/categories/{id}/` | 分类详情 |
| `PUT` / `PATCH` | `/api/categories/{id}/` | 编辑分类 |
| `DELETE` | `/api/categories/{id}/` | 删除分类 |
| `POST` | `/api/categories/{id}/disable/` | 禁用分类 |
| `POST` | `/api/categories/{id}/enable/` | 启用分类 |

### 分类类型 Category.type

| 值 | 显示 |
|----|------|
| `expense` | 支出 |
| `income` | 收入 |

### 默认支出分类
餐饮 / 交通 / 购物 / 住房 / 娱乐 / 医疗 / 学习 / 人情 / 其他

### 默认收入分类
工资 / 红包 / 兼职 / 理财收益 / 其他收入

### Category 字段

```json
{
  "id": 1,
  "book": 1,
  "name": "餐饮",
  "type": "expense",
  "type_display": "支出",
  "icon": "",
  "color": "#f44336",
  "is_active": true,
  "is_default": false,
  "budget": 800,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 4. 标签 Tag

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tags/` | 标签列表，query：`?book=1` |
| `POST` | `/api/tags/` | 新建标签（账本内同名唯一） |
| `GET` | `/api/tags/{id}/` | 标签详情 |
| `PUT` / `PATCH` | `/api/tags/{id}/` | 编辑标签 |
| `DELETE` | `/api/tags/{id}/` | 删除标签 |

### Tag 字段

```json
{
  "id": 1,
  "book": 1,
  "name": "聚餐",
  "color": "#e91e63",
  "bill_count": 3,
  "created_at": "..."
}
```

---

## 5. 账单 Bill（核心）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/bills/` | 账单列表（分页 + 多条件筛选） |
| `POST` | `/api/bills/` | 新增账单（自动更新账户余额） |
| `GET` | `/api/bills/{id}/` | 账单详情 |
| `PUT` / `PATCH` | `/api/bills/{id}/` | 编辑账单（自动回滚并重算余额） |
| `DELETE` | `/api/bills/{id}/` | 软删除（进入回收站，余额回滚） |
| `POST` | `/api/bills/batch_delete/` | 批量软删除 |
| `POST` | `/api/bills/batch_update_category/` | 批量修改分类 |
| `GET` | `/api/bills/recycle_bin/` | 回收站列表 |
| `POST` | `/api/bills/{id}/restore/` | 从回收站恢复 |
| `POST` | `/api/bills/{id}/permanent_delete/` | 彻底删除（不可恢复） |

### 5.1 列表筛选参数（全部可选，可组合）

```
GET /api/bills/
  ?book=1                 账本ID
  &type=expense           类型：expense 支出 / income 收入 / transfer 转账
  &category=1             分类ID
  &account=1              账户ID（转出或转入）
  &tag=1                  标签ID（多对多包含匹配）
  &start_date=2026-01-01  开始日期（包含）
  &end_date=2026-01-31    结束日期（包含）
  &keyword=聚餐           搜索备注内容（模糊匹配）
  &recurring=true         只看周期账单
```

### 5.2 批量操作请求体

**批量删除** `POST /api/bills/batch_delete/`
```json
{ "ids": [1, 2, 3] }
```

**批量改分类** `POST /api/bills/batch_update_category/`
```json
{ "ids": [1, 2, 3], "category_id": 2 }
```

### 5.3 账单类型 Bill.type

| 值 | 显示 | 余额影响 |
|----|------|----------|
| `expense` | 支出 | `account.balance -= amount` |
| `income` | 收入 | `account.balance += amount` |
| `transfer` | 转账 | `account.balance -= amount` & `to_account.balance += amount` |

### 5.4 周期账单字段（后续使用）

| 字段 | 说明 |
|------|------|
| `is_recurring` | 是否周期账单 |
| `recurring_type` | `none` / `daily` / `weekly` / `monthly` / `yearly` |
| `recurring_next_at` | 下次自动入账时间 |

### 5.5 Bill 字段

```json
{
  "id": 1,
  "book": 1,
  "type": "expense",
  "type_display": "支出",
  "amount": 32.5,
  "occurred_at": "2026-08-12T10:00:00Z",
  "category": 1,
  "category_name": "餐饮",
  "category_type": "expense",
  "account": 1,
  "account_name": "微信钱包",
  "to_account": null,
  "to_account_name": null,
  "remark": "午餐 麻辣烫",
  "receipt_image": "",
  "tags": [1],
  "tag_names": ["聚餐"],
  "status": "normal",
  "status_display": "正常",
  "is_recurring": false,
  "recurring_type": "none",
  "recurring_type_display": "无",
  "recurring_next_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 6. 统计报表接口

所有统计接口（除 `accounts`、`budget`）均支持时间范围参数 `?range=`：

| range | 说明 |
|-------|------|
| `today` | 今日 00:00 ~ 明日 00:00 |
| `week` | 本周一 00:00 ~ 下周一 00:00 |
| `month` | 当月1日 ~ 下月1日（默认） |
| `year` | 当年1月1日 ~ 明年1月1日 |
| `custom` | 自定义，同时传 `?start_date=&end_date=`（YYYY-MM-DD） |

---

### 6.1 收支概览

**GET** `/api/statistics/overview/`

Query：`?book=1&range=month`

```json
{
  "expense_total": 32.5,
  "income_total": 12000,
  "balance": 11967.5,
  "total_budget": 3000,
  "budget_used": 32.5,
  "budget_remaining": 2967.5,
  "budget_percent": 1.08,
  "total_account_balance": 12700,
  "account_count": 3,
  "bill_count": 2
}
```

---

### 6.2 分类饼图

**GET** `/api/statistics/pie/`

Query：`?book=1&range=month&type=expense`（`type` 默认 expense）

```json
[
  {
    "category_id": 1,
    "category_name": "餐饮",
    "color": "#f44336",
    "total": 32.5,
    "count": 1,
    "percent": 100.0
  }
]
```

---

### 6.3 收支趋势折线图

**GET** `/api/statistics/trend/`

Query：`?book=1&range=month&granularity=day`（granularity: `day` / `month`）

```json
[
  { "date": "2026-08-01", "expense": 0,     "income": 0 },
  { "date": "2026-08-02", "expense": 0,     "income": 0 },
  { "date": "2026-08-12", "expense": 32.5,  "income": 12000 }
]
```

---

### 6.4 账户余额总览

**GET** `/api/statistics/accounts/`

Query：`?book=1`

```json
[
  {
    "id": 3,
    "name": "招商银行卡",
    "type": "bank_card",
    "balance": 12000,
    "is_active": true,
    "out_count": 0,
    "in_count": 1
  },
  {
    "id": 1,
    "name": "微信钱包",
    "type": "wechat",
    "balance": 1467.5,
    "is_active": true,
    "out_count": 1,
    "in_count": 0
  }
]
```

---

### 6.5 预算进度

**GET** `/api/statistics/budget/`（仅统计当月）

Query：`?book=1`

```json
{
  "book_budget": 3000,
  "book_used": 32.5,
  "book_remaining": 2967.5,
  "book_percent": 1.08,
  "book_over_budget": false,
  "categories": [
    {
      "category_id": 1,
      "category_name": "餐饮",
      "color": "#f44336",
      "budget": 800,
      "used": 32.5,
      "remaining": 767.5,
      "percent": 4.06,
      "over_budget": false
    }
  ]
}
```

> `over_budget: true` 时前端显示红色提醒。

---

### 6.6 标签统计

**GET** `/api/statistics/tags/`

Query：`?book=1&range=month`

```json
[
  {
    "tag_id": 1,
    "tag_name": "聚餐",
    "color": "#e91e63",
    "total": 32.5,
    "count": 1
  }
]
```

---

## 7. 数据库 ER 关系

```
Book (1) ──── (N) Account
Book (1) ──── (N) Category
Book (1) ──── (N) Tag
Book (1) ──── (N) Bill

Bill (N) ──── (1) Account [account  = 转出/主账户]
Bill (N) ──── (1) Account [to_account = 转入账户，仅转账类型]
Bill (N) ──── (1) Category
Bill (N) ──── (N) Tag     [多对多，中间表 bill_tags]
```

5 张核心数据表：
- `book` 账本表
- `account` 账户表
- `category` 分类表
- `tag` 标签表
- `bill` 账单记录表
- `bill_tags` 账单-标签关联表（Django 自动生成）

---

## 8. Token 认证

### 获取 Token
```
POST /api/token/
Content-Type: application/x-www-form-urlencoded

username=admin
password=admin123
```
返回：
```json
{ "token": "3HoA0NH65QAwgzGt3acVF2Ny75v_hMkrLK4xCvXyspqpdHdX" }
```

### 使用 Token 调用接口
```http
GET /api/bills/
Authorization: Token 3HoA0NH65QAwgzGt3acVF2Ny75v_hMkrLK4xCvXyspqpdHdX
Content-Type: application/json
```

### 前端 axios 示例
```javascript
const API_BASE = 'https://squatting-agent-creed.ngrok-free.dev/api'
const TOKEN = '3HoA0NH65QAwgzGt3acVF2Ny75v_hMkrLK4xCvXyspqpdHdX'

axios.get(`${API_BASE}/bills/`, {
  headers: { Authorization: `Token ${TOKEN}` },
  params: { book: 1, type: 'expense' }
})
```

---

## 9. 功能覆盖清单

对照原始需求清单，实现情况：

| 需求模块 | 覆盖状态 |
|----------|----------|
| 1. 多账本 / 新建删除切换 / 归档 / 封面预算 | ✅ 全部接口就绪 |
| 2. 支出/收入/转账 记录 + 字段 + 修改删除 + 批量操作 | ✅ 全部就绪（转账自动更新两边余额） |
| 3. 分类默认值 + 自定义 CRUD + 图标颜色 + 启用禁用 | ✅ 全部就绪（默认分类需首次调用创建） |
| 4. 账户 5 种类型 + 初始余额 + 编辑停用 + 转账 + 余额 | ✅ 全部就绪，余额自动计算 |
| 5. 月度总预算 + 分类预算 + 进度条 + 超支提醒 | ✅ statistics/budget 已返回 percent / over_budget |
| 6. 自定义多标签 + 按标签筛选 | ✅ Tag 模型 + bill 筛选 `?tag=` + statistics/tags |
| 7. 统计报表（时间筛选/概览/饼图/折线/账户/标签） | ✅ 6 个聚合统计接口全部完成 |
| 8. 筛选搜索（时间/类型/分类/账户/标签/关键词） | ✅ bills/? 组合筛选全部就绪 |
| 9. 导入导出 Excel + 备份恢复 | ⏳ 未实现（需 openpyxl，后续补） |
| 10. 重复周期记账 | ⏳ 模型字段预留（is_recurring / recurring_type / recurring_next_at），自动生成任务未实现 |
| 11. 分页 + 详情 + 回收站（软删恢复彻底删） | ✅ 全部就绪（DRF 分页 + recycle_bin / restore / permanent_delete） |
| 12. 单用户 Token 认证 | ✅ 已启用 IsAuthenticated |
