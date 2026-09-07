# 数据分析项目测试报告

- 运行命令: `python -m pytest tests/ -v --tb=short`
- 运行时间: 2026-09-05 23:19:13
- pytest 退出码: 0

## 测试输出

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0 -- E:\�ĵ�\python_learn\python-2\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\�ĵ�
plugins: anyio-4.15.1
collecting ... collected 4 items

..\..\python_learn\python-2\tests\test_analysis.py::test_parse_amount_supports_units_and_decimal_comma PASSED [ 25%]
..\..\python_learn\python-2\tests\test_analysis.py::test_cleaning_normalizes_spaces_duplicates_and_types PASSED [ 50%]
..\..\python_learn\python-2\tests\test_analysis.py::test_real_csv_smoke PASSED [ 75%]
..\..\python_learn\python-2\tests\test_analysis.py::test_kpis_are_computable PASSED [100%]

============================== 4 passed in 1.52s ==============================
```
