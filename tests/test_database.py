import pytest

from database import (
    init_db,
    create_patient,
    get_patient,
    get_all_patients,
    update_patient,
    delete_patient,
)


@pytest.fixture
def test_db(tmp_path):
    """Create an isolated temporary database for each test."""
    db_path = str(tmp_path / "test_vitalsense.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def sample_patient():
    """Return sample data for database testing only."""
    return {
        "full_name": "Test Patient",
        "dob": "2000-08-15",
        "email": "test.patient@example.com",
        "glucose": 95.0,
        "haemoglobin": 14.5,
        "cholesterol": 180.0,
        "remarks": "Automated test record. Not medical advice.",
    }


def test_create_and_retrieve_patient(test_db, sample_patient):
    patient_id = create_patient(sample_patient, db_path=test_db)

    patient = get_patient(patient_id, db_path=test_db)

    assert patient is not None
    assert patient["full_name"] == "Test Patient"
    assert patient["email"] == "test.patient@example.com"
    assert patient["glucose"] == 95.0


def test_get_all_patients(test_db, sample_patient):
    create_patient(sample_patient, db_path=test_db)

    patients = get_all_patients(db_path=test_db)

    assert len(patients) == 1
    assert patients[0]["full_name"] == "Test Patient"


def test_search_patients_by_name_or_email(test_db, sample_patient):
    create_patient(sample_patient, db_path=test_db)

    name_results = get_all_patients(
        search_query="Test Patient",
        db_path=test_db,
    )
    email_results = get_all_patients(
        search_query="test.patient@example.com",
        db_path=test_db,
    )

    assert len(name_results) == 1
    assert len(email_results) == 1


def test_update_patient(test_db, sample_patient):
    patient_id = create_patient(sample_patient, db_path=test_db)

    updated_patient = sample_patient.copy()
    updated_patient["full_name"] = "Updated Test Patient"
    updated_patient["email"] = "updated@example.com"

    success = update_patient(
        patient_id,
        updated_patient,
        db_path=test_db,
    )

    patient = get_patient(patient_id, db_path=test_db)

    assert success is True
    assert patient["full_name"] == "Updated Test Patient"
    assert patient["email"] == "updated@example.com"


def test_delete_patient(test_db, sample_patient):
    patient_id = create_patient(sample_patient, db_path=test_db)

    success = delete_patient(patient_id, db_path=test_db)

    assert success is True
    assert get_patient(patient_id, db_path=test_db) is None


def test_update_nonexistent_patient_returns_false(test_db, sample_patient):
    success = update_patient(
        999999,
        sample_patient,
        db_path=test_db,
    )

    assert success is False


def test_delete_nonexistent_patient_returns_false(test_db):
    success = delete_patient(999999, db_path=test_db)

    assert success is False