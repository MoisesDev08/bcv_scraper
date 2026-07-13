from pandas import DataFrame

from bcv.scraper.xls_parser import XLSParser


def test_read_excel():

    parser = XLSParser(tmp_path)
    xls_paths_gen = parser.xls_paths_gen
    one_xls_path = xls_paths_gen.__next__()
    dict_sheets = parser._read_excel_sheets_generator(one_xls_path)

    for k, v in dict_sheets.items():
        assert k is not None and isinstance(k, str)
        assert v is not None and isinstance(v, DataFrame)
