"""
VitalSense AI - Database Management Layer
Provides robust, parameterized SQLite persistence with safe connection and transaction handling.
"""

from datetime import datetime, timezone
import os
import sqlite3
from typing import Dict, List, Optional, Any

# Default path points to instance/vitalsense.db relative to application root
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DEFAULT_DB_PATH = os.path.join(INSTANCE_DIR, "vitalsense.db")


def get_db_path(custom_path: Optional[str] = None) -> str:
    """Returns resolved database path, creating instance directory if needed."""
    if custom_path:
        return custom_path
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    return DEFAULT_DB_PATH


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates and returns a SQLite connection with Row factory and foreign keys enabled.
    """
    path = get_db_path(db_path)
    #Ensure the database's parent directory exists
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes SQLite database and creates the patients table if it does not exist.
    Preserves existing data across restarts.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    email TEXT NOT NULL,
                    glucose REAL NOT NULL,
                    haemoglobin REAL NOT NULL,
                    cholesterol REAL NOT NULL,
                    remarks TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Create indexes on frequently queried fields
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(full_name);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);"
            )
    finally:
        conn.close()


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Converts a SQLite row to a Python dictionary."""
    if row is None:
        return None
    return dict(row)


def create_patient(data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """
    Inserts a validated patient record into the SQLite database in a single transaction.
    
    Returns the newly inserted patient ID.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO patients (
                    full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    data["full_name"],
                    data["dob"],
                    data["email"],
                    float(data["glucose"]),
                    float(data["haemoglobin"]),
                    float(data["cholesterol"]),
                    data["remarks"],
                    now_iso,
                    now_iso,
                ),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def get_patient(patient_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single patient record by ID.
    Returns dictionary or None if not found.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, created_at, updated_at
            FROM patients
            WHERE id = ?;
            """,
            (patient_id,),
        )
        row = cursor.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_all_patients(
    search_query: Optional[str] = None, 
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves all patient records, optionally filtering by patient name or email.
    Sorted by ID descending (newest first).
    """
    conn = get_db_connection(db_path)
    try:
        if search_query and search_query.strip():
            query_str = f"%{search_query.strip()}%"
            cursor = conn.execute(
                """
                SELECT id, full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, created_at, updated_at
                FROM patients
                WHERE full_name LIKE ? OR email LIKE ?
                ORDER BY id DESC;
                """,
                (query_str, query_str),
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, created_at, updated_at
                FROM patients
                ORDER BY id DESC;
                """
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_patient(
    patient_id: int, 
    data: Dict[str, Any], 
    db_path: Optional[str] = None
) -> bool:
    """
    Updates an existing patient record in a single transaction.
    Automatically refreshes updated_at timestamp.
    
    Returns True if record was found and updated, False otherwise.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE patients
                SET full_name = ?,
                    dob = ?,
                    email = ?,
                    glucose = ?,
                    haemoglobin = ?,
                    cholesterol = ?,
                    remarks = ?,
                    updated_at = ?
                WHERE id = ?;
                """,
                (
                    data["full_name"],
                    data["dob"],
                    data["email"],
                    float(data["glucose"]),
                    float(data["haemoglobin"]),
                    float(data["cholesterol"]),
                    data["remarks"],
                    now_iso,
                    patient_id,
                ),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def delete_patient(patient_id: int, db_path: Optional[str] = None) -> bool:
    """
    Deletes a patient record by ID.
    
    Returns True if record was deleted, False if ID not found.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                "DELETE FROM patients WHERE id = ?;",
                (patient_id,),
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates live dashboard statistics from database records.
    Handles empty database gracefully without hardcoding statistics.
    
    Returns:
        total_patients: int
        avg_glucose: Optional[float] (rounded to 1 decimal place)
        avg_haemoglobin: Optional[float] (rounded to 1 decimal place)
        avg_cholesterol: Optional[float] (rounded to 1 decimal place)
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT 
                COUNT(*) AS total_count,
                AVG(glucose) AS avg_glucose,
                AVG(haemoglobin) AS avg_haemoglobin,
                AVG(cholesterol) AS avg_cholesterol
            FROM patients;
            """
        )
        row = cursor.fetchone()
        if not row or row["total_count"] == 0:
            return {
                "total_patients": 0,
                "avg_glucose": None,
                "avg_haemoglobin": None,
                "avg_cholesterol": None,
            }

        return {
            "total_patients": row["total_count"],
            "avg_glucose": round(row["avg_glucose"], 1) if row["avg_glucose"] is not None else None,
            "avg_haemoglobin": round(row["avg_haemoglobin"], 1) if row["avg_haemoglobin"] is not None else None,
            "avg_cholesterol": round(row["avg_cholesterol"], 1) if row["avg_cholesterol"] is not None else None,
        }
    finally:
        conn.close()
