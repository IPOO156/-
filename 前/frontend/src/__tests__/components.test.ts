import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PageHeader from '@/components/PageHeader.vue'
import TableSkeleton from '@/components/TableSkeleton.vue'
import FormField from '@/components/FormField.vue'
import PaginationBar from '@/components/PaginationBar.vue'

/** 抽离的通用组件：验证渲染契约，避免回归 */
describe('PageHeader', () => {
  it('渲染标题/副题/落款与操作插槽', () => {
    const w = mount(PageHeader, {
      props: { title: '记账', sub: '笔笔有据', dateline: '共 10 条记录' },
      slots: { default: '<button class="act">记一笔</button>' },
    })
    expect(w.find('.page-title').text()).toBe('记账')
    expect(w.find('.page-sub').text()).toBe('笔笔有据')
    expect(w.find('.dateline').text()).toContain('共 10 条记录')
    expect(w.find('.head-actions button.act').text()).toBe('记一笔')
  })

  it('无操作插槽时不渲染 head-actions', () => {
    const w = mount(PageHeader, { props: { title: '无操作' } })
    expect(w.find('.head-actions').exists()).toBe(false)
  })
})

describe('TableSkeleton', () => {
  it('渲染指定数量的骨架行，默认 3', () => {
    expect(mount(TableSkeleton).findAll('.skeleton')).toHaveLength(3)
    expect(mount(TableSkeleton, { props: { rows: 5 } }).findAll('.skeleton')).toHaveLength(5)
  })
})

describe('FormField', () => {
  it('渲染标签 + 控件插槽 + 错误文案', () => {
    const w = mount(FormField, {
      props: { label: '金额', error: '请输入大于 0 的金额' },
      slots: { default: '<input class="input" />' },
    })
    expect(w.find('.field-label').text()).toBe('金额')
    expect(w.find('input.input').exists()).toBe(true)
    expect(w.find('.field-error').text()).toBe('请输入大于 0 的金额')
  })

  it('有错误时不显示 hint；无错误显示 hint', () => {
    const withErr = mount(FormField, {
      props: { label: 'x', error: '错了', hint: '提示' },
    })
    expect(withErr.find('.field-error').exists()).toBe(true)
    expect(withErr.find('.field-hint').exists()).toBe(false)

    const withHint = mount(FormField, { props: { label: 'x', hint: '提示' } })
    expect(withHint.find('.field-hint').text()).toBe('提示')
  })

  it('span=2 时应用跨列样式', () => {
    const w = mount(FormField, { props: { label: 'x', span: 2 } })
    expect(w.attributes('style')).toContain('span 2')
  })
})

describe('PaginationBar', () => {
  it('展示总数与当前页码', () => {
    const w = mount(PaginationBar, {
      props: { page: 2, size: 10, total: 25, pages: 3 },
      global: { stubs: { SvgIcon: true } },
    })
    expect(w.find('.pagination-info').text()).toContain('共 25 条')
    expect(w.find('.pagination-info').text()).toContain('第 2/3 页')
  })

  it('点击页码 emit update:page', async () => {
    const w = mount(PaginationBar, {
      props: { page: 1, size: 10, total: 25, pages: 3 },
      global: { stubs: { SvgIcon: true } },
    })
    const buttons = w.findAll('.pagination-btn')
    // 数字按钮：1 / 2 / 3
    const page2 = buttons.find((b) => b.text() === '2')
    await page2!.trigger('click')
    expect(w.emitted('update:page')).toEqual([[2]])
  })

  it('首页时上一页禁用', () => {
    const w = mount(PaginationBar, {
      props: { page: 1, size: 10, total: 25, pages: 3 },
      global: { stubs: { SvgIcon: true } },
    })
    const prev = w.findAll('.pagination-btn').find((b) => b.attributes('aria-label') === '上一页')
    expect(prev!.attributes('disabled')).toBeDefined()
  })
})
