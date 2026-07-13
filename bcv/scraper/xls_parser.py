import logging
import re
from datetime import datetime
from pathlib import Path
from re import Pattern
from typing import Any, Generator

import pandas as pd
from dateutil.parser import ParserError, parse
from pandas import DataFrame
from pandas._libs import NaTType
from pandas._typing import Scalar
from python_calamine import CalamineWorkbook

from bcv.config.config import (
    # FECHA_OPER_PATTERN_XLS_ROW,
    FECHA_VALOR_PATTERN_XLS_ROW,
    TASA_DOLAR_PATTERN_XLS_ROW,
    XLS_HISTORY_DIR,
)
from bcv.scraper.exceptions import ReadingExcelError, XLSParserError

logger = logging.getLogger(__name__)
debug_enabled_bool = logger.isEnabledFor(logging.DEBUG)


class XLSParser:
    def __init__(self, path: Path):
        self._xls_paths_gen = path.iterdir()

    @property
    def xls_paths_gen(self):
        return self._xls_paths_gen

    def _read_excel_sheets_generator(
        self, xls_path: Path
    ) -> Generator[tuple[str, DataFrame], Any, Any]:
        try:
            if not xls_path.exists():
                raise FileNotFoundError

            if xls_path.is_dir():
                raise IsADirectoryError

            wb = CalamineWorkbook.from_path(xls_path)
            for sheet_name in wb.sheet_names:
                rows = wb.get_sheet_by_name(sheet_name).to_python()
                df = pd.DataFrame(rows)
                yield (sheet_name, df)

        except Exception as e:
            if debug_enabled_bool:
                logger.debug(f"path=({xls_path})\nname=({xls_path.name})")
            raise ReadingExcelError(
                mensaje=f"Error al leer archivo Excel: {xls_path.name}"
            ) from e

    def _mask_helper(
        self,
        df_str: DataFrame,
        pat: str | Pattern[str],
        case: bool = False,
        flags: int = 0,
        na: Scalar | NaTType | None = None,
        regex: bool = True,
    ):

        def func(col: pd.Series):
            return col.astype(str).str.contains(
                pat=pat, case=case, flags=flags, na=na, regex=regex
            )

        return df_str.apply(func)

    def _exctract_dolar_rate_from_row(self, df_str: DataFrame, dolar_row_df: DataFrame):

        dolar_row = dolar_row_df.iloc[0]
        rate_col_mask = self._mask_helper(df_str, r"venta", case=False)
        rate_col_df_bool = df_str[rate_col_mask].any(axis=0)
        rates = dolar_row[rate_col_df_bool]

        def func(cell):
            return abs(float(cell) - 1) > 1e-04

        rates_mask = rates.apply(func)
        rate = rates[rates_mask]

        if isinstance(rate, pd.Series):
            rate = rate.astype(float).iat[0]

        else:
            raise ValueError(f"Strange object captured instead dolar rate;{rate}")
        if not isinstance(rate, (float, int)):
            try:
                float(rate)
            except (ValueError, TypeError):
                raise ValueError(
                    f"str | int | float expected.\nTasa del dolar extraida: {rate}, tipo; {type(rate)}"
                )

        return float(rate)

    def _fecha_valor_parser(self, raw_fecha_valor: str):

        pattern = re.compile(r"(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
        date_value_match = re.search(pattern, raw_fecha_valor)
        if not date_value_match:
            raise ValueError(f"No se encontró fecha, string: {raw_fecha_valor}")

        date_value = date_value_match.group()

        return parse(date_value, dayfirst=True)

    def _exctract_date_value_from_row(self, df_str: DataFrame, date_row: DataFrame):

        date_row = date_row.iloc[0]
        date_col_mask = self._mask_helper(
            df_str, pat=r"(?:fecha)[/.\s]*(?:valor)", case=False
        )
        date_col_df_bool = df_str[date_col_mask].any(axis=0)

        df_fechas = date_row[date_col_df_bool]
        mask_fecha_valor = (
            df_fechas.astype(str).squeeze().str.contains(r"valor", case=False, na=None)
        )
        fecha_valor = df_fechas[mask_fecha_valor].squeeze()

        if not isinstance(fecha_valor, str):
            raise TypeError(f"Str expected, {type(fecha_valor).__name__} gotten")

        return self._fecha_valor_parser(fecha_valor)

    def _extract_data_rows_from_df(self, sheet_name: str, df: DataFrame):
        try:
            df_str = df.astype(str)

            # mask_fecha_oper = self._mask_helper(df_str, FECHA_OPER_PATTERN_XLS_ROW)
            # --- VALIDAR QUE HAYA SOLO UNA FILA CAPTURADA EN EL DF ---
            mask_fecha_valor = self._mask_helper(
                df_str=df_str, pat=FECHA_VALOR_PATTERN_XLS_ROW
            )
            mask_dolar_rate = self._mask_helper(df_str, TASA_DOLAR_PATTERN_XLS_ROW)

            # fecha_oper_row = df[df[mask_fecha_oper].any(axis=1)]
            # --- FALTA VALIDAR QUE SEA UNA SOLA FILA CAPTURADA ---
            fecha_valor_row = df[df[mask_fecha_valor].any(axis=1)]
            dolar_rate_row = df[df[mask_dolar_rate].any(axis=1)]

            dolar_rate = self._exctract_dolar_rate_from_row(df_str, dolar_rate_row)
            date_value = self._exctract_date_value_from_row(df_str, fecha_valor_row)
            return (date_value, dolar_rate)

        except Exception as e:
            raise XLSParserError(
                mensaje=f"Error during data extraction from excel file:\n{e}",
                sheet_name=sheet_name,
                df=df,
            ) from e

    def run(self):

        for xls in self.xls_paths_gen:
            try:
                sheets_generator = self._read_excel_sheets_generator(xls_path=xls)
                for name, df in sheets_generator:
                    # with warnings.catch_warnings():
                    #     warnings.filterwarnings(
                    #         "ignore",
                    #         message="This pattern has match groups",
                    #         category=UserWarning,
                    #     )

                    data: tuple[datetime, float] = self._extract_data_rows_from_df(
                        sheet_name=name, df=df
                    )

                    yield data

            except XLSParserError as e:
                logger.fatal(f"Error crítico al leer archivo excel:\n{str(e)}")

            except (ValueError, TypeError, ParserError) as e:
                logger.fatal(f"Error crítico al parsear datos:\n{str(e)}")
                if debug_enabled_bool:
                    logger.debug(f"xls_path=({xls})\nsheet_name=({name})")


if __name__ == "__main__":
    from bcv.config.config import XLS_HISTORY_DIR
    from bcv.scraper.http_client import HttpClient
    from bcv.scraper.pipeline import download_all_rate_history_files

    debug_enabled_bool = True
    t_dwld_start = __import__("time").perf_counter()
    download_all_rate_history_files(
        path=XLS_HISTORY_DIR, client=HttpClient(), mkdir=True
    )
    t_dwld_finish = __import__("time").perf_counter()

    tiempo_de_descarga_de_todo_el_historial = abs(t_dwld_finish - t_dwld_start)
    print(tiempo_de_descarga_de_todo_el_historial)

    parser = XLSParser()
    data_generator = parser.run()
    json_data = {}

    t_start = __import__("time").perf_counter()

    for date, rate in data_generator:
        date_key = date.strftime("%d_%m_%Y")
        json_data[date_key] = {"usd": {"venta": rate}}

    t_finish = __import__("time").perf_counter()
    t_ex = t_finish - t_start
    print(t_ex)
    print(json_data.get("30_06_2026"))
    print(len(json_data))
# Compilar regex
# Evitar .apply() y usar vectorización pura
# Evitar .squeeze()
# Validar filas/columnas únicas
# Eliminar pandas.read_excel(), pasar hojas manualmente a pandas con lazy loading
