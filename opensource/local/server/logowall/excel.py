"""Excel (.xlsx) import/export with openpyxl (no pandas/numpy dependency)."""
import io
import re
from datetime import date, datetime
from typing import Iterator, List, Optional

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

COMPANY_COLS = ['租客/买方', '公司', 'company', '客户', '品牌']
OFFICE_COLS = ['办公室（城市）', '办公室', 'office_code', '城市代码']
DEPT_COLS = ['申报部门（合并）', '部门', '业务线', 'departments']
OWNER_COLS = ['业务负责人（合并）', '负责人', 'owners']
COOP_COLS = ['合作时间', '开始合作时间', '成交时间', 'cooperation_date']

EXPORT_HEADERS = ['租客/买方', '办公室（城市）', '区域', '申报部门（合并）', '业务负责人（合并）', '合作时间']


class ExcelError(ValueError):
    pass


def _clean(v):
    """Normalise a cell: blanks -> None, integral floats -> int."""
    if v is None:
        return None
    if isinstance(v, float):
        if v != v:  # NaN
            return None
        if v.is_integer():
            return int(v)
    if isinstance(v, str) and not v.strip():
        return None
    return v


def read_rows(content: bytes) -> Iterator[dict]:
    """Yield one dict per data row with keys company/office/depts/owners/coop.

    Columns are matched by header name; when a header is missing the column
    position (0..4) is used, matching the original template layout.
    """
    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as e:
        raise ExcelError(f'Not a valid .xlsx file: {e}')
    try:
        ws = wb.worksheets[0]
        rows = ws.iter_rows(values_only=True)
        header = next(rows, None)
        if not header or len(header) < 2:
            raise ExcelError('Excel must have at least 2 columns')
        cols = {str(c).strip(): i for i, c in enumerate(header) if c is not None}

        def pick(row, names, idx):
            for name in names:
                i = cols.get(name)
                if i is not None and i < len(row):
                    v = _clean(row[i])
                    if v is not None:
                        return v
            if idx < len(row):
                return _clean(row[idx])
            return None

        for row in rows:
            if not row or all(_clean(v) is None for v in row):
                continue
            yield {
                'company': pick(row, COMPANY_COLS, 0),
                'office': pick(row, OFFICE_COLS, 1),
                'depts': pick(row, DEPT_COLS, 2),
                'owners': pick(row, OWNER_COLS, 3),
                'coop': pick(row, COOP_COLS, 4),
            }
    finally:
        wb.close()


def write_rows(rows: List[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Clients'
    ws.append(EXPORT_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row)
    widths = [36, 14, 8, 20, 24, 14]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(ord('A') + i)].width = w
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def normalize_date(v) -> str:
    """Normalize a cooperation date to YYYY-MM-DD when possible.

    Accepts datetime/date objects or strings. Partial values like '2024' or
    '2024-03' are kept as-is. Empty/invalid values become ''.
    """
    if v is None:
        return ''
    if isinstance(v, (datetime, date)):
        return v.strftime('%Y-%m-%d')
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    if not s or s.lower() in ('nan', 'nat', 'none', 'null'):
        return ''
    if re.match(r'^\d{4}(-\d{2}){0,2}$', s):
        return s
    for fmt in ('%Y/%m/%d', '%Y.%m.%d', '%Y年%m月%d日', '%Y-%m-%d', '%Y/%m', '%Y.%m',
                '%Y-%m-%d %H:%M:%S'):
        try:
            full = fmt.endswith(('%d', '日', '%S'))
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d' if full else '%Y-%m')
        except ValueError:
            continue
    return s


def opt_str(v: Optional[object]) -> str:
    return '' if v is None else str(v).strip()
