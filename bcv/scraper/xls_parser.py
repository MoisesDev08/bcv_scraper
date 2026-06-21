from bcv.config import (
    XLS_HISTORY_DIR, 
    FECHA_VALOR_PATTERN_XLS_ROW, 
    FECHA_OPER_PATTERN_XLS_ROW, 
    TASA_DOLAR_PATTERN_XLS_ROW
)
from bcv.scraper.exceptions import ReadingExcelError, XLSParserError
from pathlib import Path
from pandas import DataFrame
from pandas._typing import Scalar
from pandas._libs import NaTType
from re import Pattern
from datetime import datetime
from dateutil.parser import parse
import pandas as pd
import re

class XLSParser:
    def __init__(self):
        self._xls_paths_gen = XLS_HISTORY_DIR.iterdir()

    @property
    def xls_paths_gen(self):
        return self._xls_paths_gen
    
    def _read_excel_helper(self, xls_path: Path) ->  dict[str, DataFrame]:
        try:

            if not xls_path.exists():
                raise FileNotFoundError
            
            if xls_path.is_dir():
                raise IsADirectoryError
            
            sheets_dict: dict[str, DataFrame] = pd.read_excel(
                io=xls_path, 
                sheet_name=None, 
                header=None, 
                engine='calamine'
                )
            
            return sheets_dict
            
        except Exception as e: 
            raise ReadingExcelError(
                path=xls_path,
                name=xls_path.name
            ) from e

    def _mask_helper(
            self,
            df_str: DataFrame,
            pat: str | Pattern[str],
            case: bool = False,
            flags: int = 0,
            na: Scalar | NaTType | None = None,
            regex: bool = True
            ):
        
        func = lambda col: col.astype(str).str.contains(pat=pat, case=case, flags=flags, na=na, regex=regex)
        return df_str.apply(func)
    
    def _exctract_dolar_rate_from_row(self, df_str: DataFrame, dolar_row_df: DataFrame):

        dolar_row = dolar_row_df.iloc[0]
        rate_col_mask = self._mask_helper(df_str, r'venta', case=False)
        rate_col_df_bool = df_str[rate_col_mask].any(axis=0)

        rates = dolar_row[rate_col_df_bool]
        func = lambda cell: abs(float(cell) - 1) > 1e-04
        rates_mask = rates.apply(func)
        rate = rates[rates_mask].squeeze()

        if not isinstance(rate, (float, int)):
            if rate.isnumeric: float(rate)
            else: raise TypeError

        return rate
    
    def _fecha_valor_parser(self, raw_fecha_valor: str):

        pattern = r'(\d{2}/\d{2}/\d{4})'
        date_value_match = re.search(pattern, raw_fecha_valor, flags=re.IGNORECASE)
        date_value = date_value_match.group()

        return parse(date_value, dayfirst=True)
        

    def _exctract_date_value_from_row(self, df_str: DataFrame, date_row: DataFrame):

        date_row = date_row.iloc[0]
        date_col_mask = self._mask_helper(df_str, pat=r"fecha[/.\s]*valor", case=False)
        date_col_df_bool = df_str[date_col_mask].any(axis=0)

        df_fechas = date_row[date_col_df_bool]
        mask_fecha_valor = df_fechas.astype(str).squeeze().str.contains(r"valor", case=False, na=None)
        fecha_valor = df_fechas[mask_fecha_valor].squeeze()

        if not isinstance(fecha_valor, str):
            raise TypeError
        
        return self._fecha_valor_parser(fecha_valor)
        
    def _extract_data_rows_from_df(self, sheet_name: str, df: DataFrame):
        try:

            df_str = df.astype(str)

            mask_fecha_valor = self._mask_helper(df_str=df_str, pat=FECHA_VALOR_PATTERN_XLS_ROW)
            mask_fecha_oper = self._mask_helper(df_str, FECHA_OPER_PATTERN_XLS_ROW)
            mask_dolar_rate = self._mask_helper(df_str, TASA_DOLAR_PATTERN_XLS_ROW)

            fecha_valor_row = df[df[mask_fecha_valor].any(axis=1)]
            fecha_oper_row = df[df[mask_fecha_oper].any(axis=1)]
            dolar_rate_row = df[df[mask_dolar_rate].any(axis=1)]
            
            dolar_rate = self._exctract_dolar_rate_from_row(df_str, dolar_rate_row)
            date_value = self._exctract_date_value_from_row(df_str, fecha_valor_row)
            return (date_value, dolar_rate)
            
        
        except Exception as e:
            raise XLSParserError(
                mensaje="Error during data extraction from excel file", 
                sheet_name=sheet_name, 
                df=df
                )
            

    def run(self):

        for xls in self.xls_paths_gen:
            try:
                sheets_dict = self._read_excel_helper(xls_path=xls)
                for name, df in sheets_dict.items():

                    data: tuple[datetime, float] = self._extract_data_rows_from_df(sheet_name=name, df=df)

                    yield data
            



                ...
            except (...):
                ...

# --- Caller hardcodeado que eliminaré una vez termine el módulo ---
parser = XLSParser()
xls_path = parser.xls_paths_gen.__next__()
sheets_dict = parser._read_excel_helper(xls_path)
df_test = sheets_dict.get('31032020')
data = parser._extract_data_rows_from_df(sheet_name='31032020', df=df_test)