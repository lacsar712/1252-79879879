export interface PaginationParams {
  page: number
  page_size: number
  [key: string]: any
}

export function buildPaginationParams(
  page: number,
  pageSize: number,
  extraParams: Record<string, any> = {}
): PaginationParams {
  const params: PaginationParams = {
    page,
    page_size: pageSize
  }

  Object.entries(extraParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params[key] = value
    }
  })

  return params
}

export function buildDateRangeParams(
  dateRange: string[],
  startKey: string = 'start_date',
  endKey: string = 'end_date'
): Record<string, string> {
  const result: Record<string, string> = {}
  if (dateRange && dateRange.length === 2) {
    if (dateRange[0]) result[startKey] = dateRange[0]
    if (dateRange[1]) result[endKey] = dateRange[1]
  }
  return result
}

export function cleanParams(params: Record<string, any>): Record<string, any> {
  const result: Record<string, any> = {}
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      result[key] = value
    }
  })
  return result
}
