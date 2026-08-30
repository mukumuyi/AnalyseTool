"""proc_historyの生成ロジック本体。

品目階層（prodspec_id→mainpd_id）→設備マスタ（固定処理時間）→
ルーティング（ope_no×ope_seq）→ロット割当→ロットごとの行生成、という
順に組み立てる。行数は数万件規模を想定しており、`generate_sample_data`の
ような列ごとの一括ベクトル化はせず、ロット単位のシンプルなループで
時系列の依存関係（前工程のend_timeより後ろに次工程のstart_timeが来る）を
正しく再現する。
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pyarrow as pa

from .config import LognormalSpec, ProcHistoryConfig, TimeRange

ProdspecMaster = list[str]
MainpdMaster = dict[str, str]
"""mainpd_id -> prodspec_id"""
EqpMaster = dict[str, float]
"""eqp_id -> 固定処理時間（分）"""
Routing = dict[str, list[str]]
"""mainpd_id -> ope_noのリスト（順序がope_seqに対応）"""
OpeEqpCandidates = dict[str, list[str]]
"""ope_no -> 使用可能なeqp_idのリスト"""


def generate_table(config: ProcHistoryConfig, seed: int) -> pa.Table:
    """設定一式からproc_history全体を1つのpyarrow.Tableとして組み立てる。"""
    rng = np.random.default_rng(seed)

    prodspec_ids = _build_prodspec_master(config, rng)
    mainpd_to_prodspec = _build_mainpd_master(prodspec_ids, config, rng)
    eqp_processing_minutes = _build_eqp_master(config, rng)
    routing = _build_routing(list(mainpd_to_prodspec), config, rng)
    ope_eqp_candidates = _build_ope_eqp_candidates(
        config.ope_name_pool, list(eqp_processing_minutes), config, rng
    )
    lot_mainpd = _assign_lot_mainpd(config.lot_count, list(mainpd_to_prodspec), rng)

    rows: list[dict[str, object]] = []
    for i in range(config.lot_count):
        lot_id = f"LOT{i + 1:06d}"
        mainpd_id = lot_mainpd[i]
        prodspec_id = mainpd_to_prodspec[mainpd_id]
        lot_start_time = _sample_datetime_in_range(config.time_range, rng)
        rows.extend(
            _generate_lot_rows(
                lot_id=lot_id,
                prodspec_id=prodspec_id,
                mainpd_id=mainpd_id,
                ope_nos=routing[mainpd_id],
                ope_eqp_candidates=ope_eqp_candidates,
                eqp_processing_minutes=eqp_processing_minutes,
                queue_minutes_spec=config.queue_minutes,
                lot_start_time=lot_start_time,
                rng=rng,
            )
        )

    return _rows_to_table(rows)


def _build_prodspec_master(
    config: ProcHistoryConfig, rng: np.random.Generator
) -> ProdspecMaster:
    """`prodspec_id`（品目、親）のマスタを作る。"""
    width = len(str(config.prodspec_count))
    return [f"PS{i + 1:0{width}d}" for i in range(config.prodspec_count)]


def _build_mainpd_master(
    prodspec_ids: ProdspecMaster, config: ProcHistoryConfig, rng: np.random.Generator
) -> MainpdMaster:
    """`prodspec_id`ごとに`mainpd_id`（子）を複数生成し、親子関係を作る。"""
    mainpd_to_prodspec: MainpdMaster = {}
    counts = rng.integers(
        config.mainpd_per_prodspec.min,
        config.mainpd_per_prodspec.max + 1,
        size=len(prodspec_ids),
    )
    for prodspec_id, count in zip(prodspec_ids, counts, strict=True):
        for m in range(1, count + 1):
            mainpd_to_prodspec[f"{prodspec_id}-M{m}"] = prodspec_id
    return mainpd_to_prodspec


def _build_eqp_master(config: ProcHistoryConfig, rng: np.random.Generator) -> EqpMaster:
    """`eqp_id`（設備）のマスタを作り、設備ごとに1個だけ固定処理時間を割り当てる。"""
    width = len(str(config.eqp_count))
    eqp_ids = [f"EQP{i + 1:0{width}d}" for i in range(config.eqp_count)]
    minutes = _sample_lognormal(
        config.eqp_processing_minutes, size=config.eqp_count, rng=rng
    )
    return dict(zip(eqp_ids, minutes, strict=True))


def _build_routing(
    mainpd_ids: list[str], config: ProcHistoryConfig, rng: np.random.Generator
) -> Routing:
    """`mainpd_id`ごとに固有のルーティング（`ope_no`の並び）を組み立てる。"""
    pool = config.ope_name_pool
    routing: Routing = {}
    for mainpd_id in mainpd_ids:
        n = int(
            rng.integers(config.steps_per_routing.min, config.steps_per_routing.max + 1)
        )
        replace = n > len(pool)
        chosen = rng.choice(pool, size=n, replace=replace)
        routing[mainpd_id] = list(chosen)
    return routing


def _build_ope_eqp_candidates(
    ope_name_pool: list[str],
    eqp_ids: list[str],
    config: ProcHistoryConfig,
    rng: np.random.Generator,
) -> OpeEqpCandidates:
    """`ope_no`ごとに、使用可能な`eqp_id`の候補群を割り当てる（多対多）。"""
    k = min(config.eqp_per_ope_name, len(eqp_ids))
    return {
        ope_no: list(rng.choice(eqp_ids, size=k, replace=False))
        for ope_no in ope_name_pool
    }


def _assign_lot_mainpd(
    lot_count: int, mainpd_ids: list[str], rng: np.random.Generator
) -> list[str]:
    """ロットごとに`mainpd_id`を割り当てる（今回は一様分布）。"""
    return list(rng.choice(mainpd_ids, size=lot_count, replace=True))


def _generate_lot_rows(
    lot_id: str,
    prodspec_id: str,
    mainpd_id: str,
    ope_nos: list[str],
    ope_eqp_candidates: OpeEqpCandidates,
    eqp_processing_minutes: EqpMaster,
    queue_minutes_spec: LognormalSpec,
    lot_start_time: datetime,
    rng: np.random.Generator,
) -> list[dict[str, object]]:
    """1ロットぶんの`proc_history`行を、ルーティング順に時刻を進めながら作る。"""
    rows: list[dict[str, object]] = []
    current_start = lot_start_time
    for seq, ope_no in enumerate(ope_nos, start=1):
        eqp_id = str(rng.choice(ope_eqp_candidates[ope_no]))
        processing_minutes = eqp_processing_minutes[eqp_id]
        current_end = current_start + timedelta(minutes=processing_minutes)
        rows.append(
            {
                "lot_id": lot_id,
                "prodspec_id": prodspec_id,
                "mainpd_id": mainpd_id,
                "ope_no": ope_no,
                "ope_seq": seq,
                "eqp_id": eqp_id,
                "start_time": current_start,
                "end_time": current_end,
            }
        )
        queue_minutes = float(_sample_lognormal(queue_minutes_spec, size=1, rng=rng)[0])
        current_start = current_end + timedelta(minutes=queue_minutes)
    return rows


def _sample_lognormal(
    spec: LognormalSpec, size: int, rng: np.random.Generator
) -> np.ndarray:
    """対数正規分布から`size`個サンプリングし、`min`/`max`でクリップする。"""
    values = rng.lognormal(mean=spec.mean, sigma=spec.stddev, size=size)
    return np.clip(values, spec.min, spec.max)


def _sample_datetime_in_range(
    time_range: TimeRange, rng: np.random.Generator
) -> datetime:
    """`time_range`内の日時を一様乱数で1つサンプリングする。"""
    start = datetime.fromisoformat(time_range.start)
    end = datetime.fromisoformat(time_range.end)
    span_seconds = (end - start).total_seconds()
    offset_seconds = float(rng.uniform(0, span_seconds))
    return start + timedelta(seconds=offset_seconds)


def _rows_to_table(rows: list[dict[str, object]]) -> pa.Table:
    """行の辞書リストを、列指向の`pyarrow.Table`に変換する。"""
    if not rows:
        raise ValueError(
            "生成された行が0件です（lot_countまたはルーティング設定を確認してください）"
        )
    columns = {key: [row[key] for row in rows] for key in rows[0]}
    schema = pa.schema(
        [
            ("lot_id", pa.string()),
            ("prodspec_id", pa.string()),
            ("mainpd_id", pa.string()),
            ("ope_no", pa.string()),
            ("ope_seq", pa.int64()),
            ("eqp_id", pa.string()),
            ("start_time", pa.timestamp("us")),
            ("end_time", pa.timestamp("us")),
        ]
    )
    return pa.table(columns, schema=schema)
