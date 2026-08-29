"""データ定義情報（プロファイル）の共通フォーマット。

各ツールの `prepare.py`（EDA）は、読み込んだ実データの傾向（件数・欠損率・
分布・カテゴリ値など）をこのフォーマットのJSONとして書き出す想定。
`generate_sample_data` ツールは同じフォーマットのJSONを読み込み、それを
「データ定義情報」としてサンプルデータを生成する。

つまりこのモジュールが定義する `DatasetProfile` / `ColumnProfile` が、
プロファイリング（分析）とサンプルデータ生成の間の共通の契約になる。
プロファイルは実データから `profile_from_parquet()` で自動生成することも、
人が直接JSONを書く／編集することもできる。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

ColumnRole = Literal["id", "numeric", "categorical", "date", "boolean"]
NumericDistribution = Literal["uniform", "normal", "lognormal"]


@dataclass
class CategoryFreq:
    """カテゴリ値1件と、その出現割合（0.0〜1.0）。"""

    value: str
    freq: float


@dataclass
class ColumnProfile:
    """1列ぶんのデータ定義情報。

    `role` によって使うフィールドが変わる。

    - `id`       : 連番を振る。文字列IDにしたい場合は `categories` の
                   先頭1件の `value` を接頭辞として使う（例: "顧客" → 顧客000001）。
    - `numeric`  : `distribution` に従って `min`/`max`/`mean`/`stddev` の
                   範囲で値を生成する。`lognormal` の `mean`/`stddev` は
                   対数正規分布の元になる正規分布側のパラメータ（実際の
                   値の平均・標準偏差ではない）。
    - `categorical`: `categories` から出現割合に従って値を選ぶ。
    - `date`     : `min`/`max`（"YYYY-MM-DD"）の範囲で一様に日付を生成する。
    - `boolean`  : `true_rate` の確率で True にする。
    """

    name: str
    dtype: str
    role: ColumnRole
    description: str = ""
    null_rate: float = 0.0

    # numeric 用
    min: float | int | str | None = None
    max: float | int | str | None = None
    mean: float | None = None
    stddev: float | None = None
    distribution: NumericDistribution = "uniform"

    # categorical 用
    categories: list[CategoryFreq] = field(default_factory=list)

    # boolean 用
    true_rate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ColumnProfile:
        d = dict(d)
        categories = [CategoryFreq(**c) for c in d.get("categories", [])]
        d["categories"] = categories
        return ColumnProfile(**d)


@dataclass
class DatasetProfile:
    """1テーブルぶんのデータ定義情報（列プロファイルの集まり）。"""

    name: str
    row_count: int
    columns: list[ColumnProfile]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "row_count": self.row_count,
            "columns": [c.to_dict() for c in self.columns],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> DatasetProfile:
        columns = [ColumnProfile.from_dict(c) for c in d["columns"]]
        return DatasetProfile(name=d["name"], row_count=d["row_count"], columns=columns)


def save_profile(profile: DatasetProfile, path: str | Path) -> None:
    """プロファイルをJSONファイルに保存する（`prepare.py` の出力用）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_profile(path: str | Path) -> DatasetProfile:
    """JSONファイルからプロファイルを読み込む（`generate_sample_data` の入力用）。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return DatasetProfile.from_dict(data)


def profile_from_parquet(
    path: str | Path,
    name: str | None = None,
    max_categories: int = 50,
) -> DatasetProfile:
    """Parquetファイルの中身をDuckDBで集計し、DatasetProfileを作る。

    `prepare.py`（EDA）はこの関数を呼んで実データの傾向を求め、
    `save_profile()` でJSONとして残す想定。列ごとの役割（role）は
    型と distinct 件数から簡易的に推定する。
    """
    import duckdb

    path = Path(path)
    name = name or path.stem
    con = duckdb.connect()
    rel = f"read_parquet('{path.as_posix()}')"
    row_count: int = con.sql(f"SELECT COUNT(*) FROM {rel}").fetchone()[0]

    schema_rows = con.sql(f"DESCRIBE SELECT * FROM {rel}").fetchall()

    columns: list[ColumnProfile] = []
    for col_name, col_type, *_ in schema_rows:
        quoted = f'"{col_name}"'
        null_rate = (
            con.sql(
                f"SELECT AVG(CASE WHEN {quoted} IS NULL THEN 1.0 ELSE 0.0 END) FROM {rel}"
            ).fetchone()[0]
            or 0.0
        )
        upper_type = col_type.upper()

        if "DATE" in upper_type or "TIMESTAMP" in upper_type:
            lo, hi = con.sql(f"SELECT MIN({quoted}), MAX({quoted}) FROM {rel}").fetchone()
            columns.append(
                ColumnProfile(
                    name=col_name,
                    dtype=col_type.lower(),
                    role="date",
                    null_rate=null_rate,
                    min=str(lo),
                    max=str(hi),
                )
            )
            continue

        if upper_type == "BOOLEAN":
            true_rate = (
                con.sql(
                    f"SELECT AVG(CASE WHEN {quoted} THEN 1.0 ELSE 0.0 END) FROM {rel}"
                ).fetchone()[0]
                or 0.0
            )
            columns.append(
                ColumnProfile(
                    name=col_name,
                    dtype="bool",
                    role="boolean",
                    null_rate=null_rate,
                    true_rate=true_rate,
                )
            )
            continue

        distinct_count: int = con.sql(
            f"SELECT approx_count_distinct({quoted}) FROM {rel}"
        ).fetchone()[0]
        is_numeric_type = any(
            t in upper_type for t in ("INT", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT")
        )

        if is_numeric_type and distinct_count > max_categories:
            # distinct_count は approx_count_distinct（HyperLogLog）による概算値で、
            # 数%程度の誤差が出るため、閾値は 0.99 ではなく余裕を持って 0.9 にする。
            looks_like_id = col_name.lower().endswith("id") and distinct_count >= row_count * 0.9
            if looks_like_id:
                columns.append(
                    ColumnProfile(name=col_name, dtype=col_type.lower(), role="id", null_rate=null_rate)
                )
                continue
            lo, hi, mean, stddev = con.sql(
                f"SELECT MIN({quoted}), MAX({quoted}), AVG({quoted}), STDDEV_SAMP({quoted}) FROM {rel}"
            ).fetchone()
            columns.append(
                ColumnProfile(
                    name=col_name,
                    dtype=col_type.lower(),
                    role="numeric",
                    null_rate=null_rate,
                    min=lo,
                    max=hi,
                    mean=mean,
                    stddev=stddev,
                    distribution="normal",
                )
            )
            continue

        # 残りは文字列 or 値の種類が少ない数値 → カテゴリカル扱い
        top = con.sql(
            f"SELECT {quoted}, COUNT(*) AS n FROM {rel} "
            f"WHERE {quoted} IS NOT NULL "
            f"GROUP BY {quoted} ORDER BY n DESC LIMIT {max_categories}"
        ).fetchall()
        total = sum(n for _, n in top) or 1
        categories = [CategoryFreq(value=str(v), freq=n / total) for v, n in top]
        columns.append(
            ColumnProfile(
                name=col_name,
                dtype=col_type.lower(),
                role="categorical",
                null_rate=null_rate,
                categories=categories,
            )
        )

    con.close()
    return DatasetProfile(name=name, row_count=row_count, columns=columns)
