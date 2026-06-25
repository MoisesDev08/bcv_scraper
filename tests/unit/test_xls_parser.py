import sys
from bcv.scraper.xls_parser import XLSParser
from pandas import DataFrame

def test_read_excel():

    parser = XLSParser()
    xls_paths_gen = parser.xls_paths_gen
    one_xls_path = xls_paths_gen.__next__()
    dict_sheets = parser._read_excel_helper(one_xls_path)

    for k, v in dict_sheets.items():
        assert k is not None and isinstance(k, str)
        assert v is not None and isinstance(v, DataFrame)
    