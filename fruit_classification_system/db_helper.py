import json
from typing import Any, Dict, Optional

import pymysql


class MySQLConnectionManager:
    """Lightweight connection manager for MySQL using PyMySQL.

    This is intentionally simple: open one connection per instance.
    For GUI apps, reuse a single instance to avoid excessive connections.
    """

    def __init__(self, config: Dict[str, Any]):
        db_cfg = config.get("database", {})
        self._connection = pymysql.connect(
            host=db_cfg.get("host", "127.0.0.1"),
            port=int(db_cfg.get("port", 3307)),
            user=db_cfg.get("user", "root"),
            password=db_cfg.get("password", ""),
            database=db_cfg.get("database", "fruit_classification"),
            connect_timeout=int(db_cfg.get("connect_timeout", 10)),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def cursor(self):
        return self._connection.cursor()

    def close(self):
        try:
            self._connection.close()
        except Exception:
            pass


def ensure_product_exists(db: MySQLConnectionManager, name: str, description: Optional[str] = None) -> int:
    with db.cursor() as cur:
        cur.execute("SELECT id FROM products WHERE name=%s", (name,))
        row = cur.fetchone()
        if row:
            return int(row["id"])
        cur.execute(
            "INSERT INTO products(name, description) VALUES(%s, %s)",
            (name, description),
        )
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        return int(cur.fetchone()["id"])


def insert_capture(db: MySQLConnectionManager, product_id: int, source: Optional[str] = None, image_path: Optional[str] = None) -> int:
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO captures(product_id, source, image_path) VALUES(%s, %s, %s)",
            (product_id, source, image_path),
        )
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        return int(cur.fetchone()["id"])


def insert_classification(
    db: MySQLConnectionManager,
    capture_id: int,
    product_id: int,
    size_label: Optional[str] = None,
    ripeness_label: Optional[str] = None,
    defect_detected: bool = False,
    defect_area_ratio: Optional[float] = None,
    color_ratio_red: Optional[float] = None,
    color_ratio_green: Optional[float] = None,
    a_star_value: Optional[float] = None,
    b_star_value: Optional[float] = None,
    confidence: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> int:
    extra_json = json.dumps(extra) if extra is not None else None
    with db.cursor() as cur:
        cur.execute(
            (
                "INSERT INTO classifications("
                "capture_id, product_id, size_label, ripeness_label, defect_detected, "
                "defect_area_ratio, color_ratio_red, color_ratio_green, a_star_value, b_star_value, "
                "confidence, extra"
                ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            ),
            (
                capture_id,
                product_id,
                size_label,
                ripeness_label,
                1 if defect_detected else 0,
                defect_area_ratio,
                color_ratio_red,
                color_ratio_green,
                a_star_value,
                b_star_value,
                confidence,
                extra_json,
            ),
        )
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        return int(cur.fetchone()["id"])


def load_config(path: str = "config.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_recent_classifications(db: MySQLConnectionManager, limit: int = 100):
    """Fetch recent classification rows with product and capture info."""
    sql = (
        "SELECT c.id, c.created_at, p.name AS product, cap.image_path, "
        "c.size_label, c.ripeness_label, c.defect_detected, c.confidence "
        "FROM classifications c "
        "JOIN captures cap ON c.capture_id = cap.id "
        "JOIN products p ON c.product_id = p.id "
        "ORDER BY c.id DESC LIMIT %s"
    )
    with db.cursor() as cur:
        cur.execute(sql, (int(limit),))
        return cur.fetchall()


def fetch_captures_with_counts(
    db: MySQLConnectionManager,
    product: Optional[str] = None,
    session_like: Optional[str] = None,
    limit: int = 500,
):
    """List recent captures with item counts and basic info."""
    clauses = []
    params: list[Any] = []
    if product:
        clauses.append("p.name = %s")
        params.append(product)
    if session_like:
        clauses.append("cap.source LIKE %s")
        params.append(f"%{session_like}%")
    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = (
        "SELECT cap.id, cap.captured_at, cap.source, cap.image_path, p.name AS product, "
        "(SELECT COUNT(1) FROM classifications c WHERE c.capture_id = cap.id) AS num_items "
        "FROM captures cap JOIN products p ON cap.product_id = p.id "
        f"{where_sql} ORDER BY cap.id DESC LIMIT %s"
    )
    params.append(int(limit))
    with db.cursor() as cur:
        cur.execute(sql, tuple(params))
        return cur.fetchall()


def fetch_classifications_by_capture(db: MySQLConnectionManager, capture_id: int):
    sql = (
        "SELECT id, size_label, ripeness_label, defect_detected, confidence, created_at "
        "FROM classifications WHERE capture_id = %s ORDER BY id ASC"
    )
    with db.cursor() as cur:
        cur.execute(sql, (int(capture_id),))
        return cur.fetchall()

if __name__ == "__main__":
    cfg = load_config()
    db = MySQLConnectionManager(cfg)
    try:
        product_name = cfg.get("product", "tomato")
        product_desc = cfg.get("description")
        product_id = ensure_product_exists(db, product_name, product_desc)
        capture_id = insert_capture(db, product_id, source="manual", image_path=None)
        classification_id = insert_classification(
            db,
            capture_id=capture_id,
            product_id=product_id,
            size_label=None,
            ripeness_label=None,
            defect_detected=False,
            extra={"smoke_test": True},
        )
        print({
            "product_id": product_id,
            "capture_id": capture_id,
            "classification_id": classification_id,
        })
    finally:
        db.close()



