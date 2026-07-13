import tracemalloc

from psutil import Process

tracemalloc.start(5)
procces = Process()  # type: ignore

from pathlib import Path
from time import perf_counter

from bcv.scraper.pipeline import download_all_rate_history_files


def test_descargas(tmp_path):
    LOG_DIR = Path(__file__).parent / "log.log"

    for _ in range(30):
        fds_inicio = procces.num_fds()
        mem_inicio = procces.memory_info().rss / 1024 / 1024

        data = []
        path = tmp_path / f"{_}"
        snap_before = tracemalloc.take_snapshot()

        inicio_descarga = perf_counter()
        download_all_rate_history_files(path, mkdir=True)
        final_descarga = perf_counter()

        snap_after = tracemalloc.take_snapshot()
        tiempo_de_ejecucion = final_descarga - inicio_descarga
        data.append(f"Ejecución N°{_}")
        data.append(f"Tiempo de Ejecucion: {tiempo_de_ejecucion}")

        fds_final = procces.num_fds()
        mem_final = procces.memory_info().rss / 1024 / 1024

        diff = snap_after.compare_to(snap_before, "traceback")
        top = diff[:5]

        for stat in top:
            tr = stat.traceback.format()
            size = stat.size / 1024 / 1024
            data.append(f"Consumo de memoria de este proceso: {size:.2f}MB")
            data.append("\n".join(tr))
            data.append("\n")

        data.append(("fds_inicio", fds_inicio))
        data.append(("mem_inicio", mem_inicio))
        data.append(("fds_final", fds_final))
        data.append(("mem_final", mem_final))
        data.append(("fds_diff", fds_final - fds_inicio))
        data.append(("mem_diff", mem_final - mem_inicio))
        data.append("\n")

        for x in data:
            with LOG_DIR.open(encoding="utf-8", mode="a+") as f:
                f.write(str(x))
                f.write("\n")
        pass
