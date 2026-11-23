export function trendLabel(metric: string, values: number[]) {
  const last = values[values.length - 1]
  if (last === undefined) return `${metric}趋势：暂无数据`
  const format = (value: number) => value.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
  return `${metric}趋势，共 ${values.length} 个数据点，最低 ${format(Math.min(...values))}，最高 ${format(Math.max(...values))}，最近 ${format(last)}`
}
