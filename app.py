"""
VitalSense AI - Main Application Module
AI-Powered Patient Health Insights and Management System
"""
import markdown
import bleach
from datetime import datetime
import os
import secrets
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv

from database import (
    init_db,
    create_patient,
    get_patient,
    get_all_patients,
    update_patient,
    delete_patient,
    get_dashboard_stats,
)
from validators import (
    validate_patient_payload,
    format_dob_for_display,
    LAB_UNITS,
    LAB_LIMITS,
)
from ai_service import (
    generate_health_remarks,
    AIServiceError,
    AIConfigurationError,
)

# Load environment configuration
load_dotenv()


def create_app(test_config=None) -> Flask:
    """Application factory for VitalSense AI."""
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key or secret_key in ("replace_with_a_random_secret_key", "secret"):
        # Generate a stable secret for development if unspecified
        secret_key = "vitalsense-dev-secret-key-change-in-production-32bytes"

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=os.path.join(app.instance_path, "vitalsense.db"),
    )

    if test_config:
        app.config.update(test_config)

    # Enable CSRF Protection globally
    csrf = CSRFProtect(app)

    # Ensure database table exists
    with app.app_context():
        init_db(app.config.get("DATABASE"))

    # Custom Jinja2 Filters and Context Processors
    @app.template_filter("format_dob")
    def format_dob_filter(iso_date: str) -> str:
        return format_dob_for_display(iso_date)

    @app.template_filter("format_datetime")
    def format_datetime_filter(iso_timestamp: str) -> str:
        """Formats ISO UTC timestamp into a human-readable date and time."""
        if not iso_timestamp:
            return "N/A"
        try:
            # Handle potential ISO format with timezone or standard format
            clean_ts = iso_timestamp.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            return dt.strftime("%b %d, %Y %I:%M %p UTC")
        except Exception:
            return iso_timestamp

    @app.context_processor
    def inject_app_metadata():
        return {
            "APP_NAME": "VitalSense AI",
            "APP_FULL_TITLE": "AI-Powered Patient Health Insights and Management System",
            "APP_TAGLINE": "Smarter Health Insights. Better-Informed Decisions.",
            "LAB_UNITS": LAB_UNITS,
            "LAB_LIMITS": LAB_LIMITS,
        }

    # ------------------ Routes ------------------

    @app.route("/", methods=["GET"])
    def dashboard():
        """
        Dashboard route: displays live statistical summary and patient records list.
        Supports search by patient name or email.
        """
        db_path = app.config.get("DATABASE")
        search_query = request.args.get("q", "").strip()
        stats = get_dashboard_stats(db_path=db_path)
        patients = get_all_patients(search_query=search_query, db_path=db_path)

        return render_template(
            "index.html",
            stats=stats,
            patients=patients,
            search_query=search_query,
        )

    @app.route("/patients", methods=["GET"])
    def patients_list():
        """Alias redirecting to dashboard patient records view."""
        return redirect(url_for("dashboard"))

    @app.route("/patients/add", methods=["GET", "POST"])
    def add_patient():
        """
        Add Patient route: collects patient information and laboratory measurements.
        Validates input, calls NVIDIA NIM AI service to generate observations,
        and saves complete record in SQLite in a single transaction.
        """
        if request.method == "GET":
            return render_template(
                "add_patient.html",
                form_data={},
                errors={},
            )

        # POST submission
        form_data = {
            "full_name": request.form.get("full_name", ""),
            "dob": request.form.get("dob", ""),
            "email": request.form.get("email", ""),
            "glucose": request.form.get("glucose", ""),
            "haemoglobin": request.form.get("haemoglobin", ""),
            "cholesterol": request.form.get("cholesterol", ""),
        }

        # 1. Server-side validation
        is_valid, errors, cleaned = validate_patient_payload(form_data)
        if not is_valid:
            flash("Please correct the errors in the form before proceeding.", "danger")
            return render_template(
                "add_patient.html",
                form_data=form_data,
                errors=errors,
            ), 400

        # 2. Call NVIDIA NIM AI Service to generate remarks
        try:
            remarks = generate_health_remarks(
                glucose=cleaned["glucose"],
                haemoglobin=cleaned["haemoglobin"],
                cholesterol=cleaned["cholesterol"],
            )
        except AIConfigurationError as e:
            flash(f"AI Setup Error: {str(e)}", "danger")
            return render_template(
                "add_patient.html",
                form_data=form_data,
                errors={"ai_error": str(e)},
            ), 503
        except AIServiceError as e:
            flash(f"AI Service Failure: {str(e)} Patient record was not saved. Please retry.", "danger")
            return render_template(
                "add_patient.html",
                form_data=form_data,
                errors={"ai_error": str(e)},
            ), 502

        # 3. Save to database in a single transaction
        cleaned["remarks"] = remarks
        db_path = app.config.get("DATABASE")
        try:
            patient_id = create_patient(cleaned, db_path=db_path)
            flash("Patient record created successfully with AI-assisted health observations.", "success")
            return redirect(url_for("patient_detail", patient_id=patient_id))
        except Exception as e:
            flash(f"Database Error: Could not save patient record. {str(e)}", "danger")
            return render_template(
                "add_patient.html",
                form_data=form_data,
                errors={"db_error": "Database persistence failed."},
            ), 500

    @app.route("/patients/<int:patient_id>", methods=["GET"])
    def patient_detail(patient_id: int):
        """
        Patient Detail route: displays full record, laboratory values, and stored AI remarks.
        Does not regenerate remarks on view.
        """
        db_path = app.config.get("DATABASE")
        patient = get_patient(patient_id, db_path=db_path)
        if not patient:
            abort(404)

        return render_template("patient_detail.html", patient=patient)

    @app.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
    def edit_patient(patient_id: int):
        """
        Edit Patient route: prepopulates form with current record.
        If laboratory values changed, regenerates AI remarks before committing.
        If only non-laboratory fields (e.g. email to gokul@infocare.com) changed,
        preserves existing remarks without making an AI call.
        """
        db_path = app.config.get("DATABASE")
        existing = get_patient(patient_id, db_path=db_path)
        if not existing:
            abort(404)

        if request.method == "GET":
            # Prepopulate form (format DOB to DD/MM/YYYY for user editing)
            form_data = {
                "full_name": existing["full_name"],
                "dob": format_dob_for_display(existing["dob"]),
                "email": existing["email"],
                "glucose": str(existing["glucose"]),
                "haemoglobin": str(existing["haemoglobin"]),
                "cholesterol": str(existing["cholesterol"]),
            }
            return render_template(
                "edit_patient.html",
                patient=existing,
                form_data=form_data,
                errors={},
            )

        # POST submission
        form_data = {
            "full_name": request.form.get("full_name", ""),
            "dob": request.form.get("dob", ""),
            "email": request.form.get("email", ""),
            "glucose": request.form.get("glucose", ""),
            "haemoglobin": request.form.get("haemoglobin", ""),
            "cholesterol": request.form.get("cholesterol", ""),
        }

        # 1. Server-side validation
        is_valid, errors, cleaned = validate_patient_payload(form_data)
        if not is_valid:
            flash("Please correct the errors in the form before saving.", "danger")
            return render_template(
                "edit_patient.html",
                patient=existing,
                form_data=form_data,
                errors=errors,
            ), 400

        # 2. Check if laboratory values changed
        labs_changed = (
            abs(float(existing["glucose"]) - cleaned["glucose"]) > 1e-4
            or abs(float(existing["haemoglobin"]) - cleaned["haemoglobin"]) > 1e-4
            or abs(float(existing["cholesterol"]) - cleaned["cholesterol"]) > 1e-4
        )

        remarks = existing["remarks"]
        if labs_changed:
            # Regenerate remarks with AI
            try:
                remarks = generate_health_remarks(
                    glucose=cleaned["glucose"],
                    haemoglobin=cleaned["haemoglobin"],
                    cholesterol=cleaned["cholesterol"],
                )
            except AIServiceError as e:
                # Preserve original database record if AI fails
                flash(
                    f"AI Regeneration Failed: {str(e)} Existing record was preserved.",
                    "danger",
                )
                return render_template(
                    "edit_patient.html",
                    patient=existing,
                    form_data=form_data,
                    errors={"ai_error": str(e)},
                ), 502

        # 3. Commit update
        cleaned["remarks"] = remarks
        try:
            success = update_patient(patient_id, cleaned, db_path=db_path)
            if not success:
                abort(404)
            flash("Patient record updated successfully.", "success")
            return redirect(url_for("patient_detail", patient_id=patient_id))
        except Exception as e:
            flash(f"Database Error: Could not update patient record. {str(e)}", "danger")
            return render_template(
                "edit_patient.html",
                patient=existing,
                form_data=form_data,
                errors={"db_error": "Database update failed."},
            ), 500

    @app.route("/patients/<int:patient_id>/delete", methods=["POST"])
    def delete_patient_route(patient_id: int):
        """
        Delete Patient route: Deletes selected record via POST request with CSRF protection.
        """
        db_path = app.config.get("DATABASE")
        existing = get_patient(patient_id, db_path=db_path)
        if not existing:
            flash("Cannot delete: Patient record not found.", "warning")
            return redirect(url_for("dashboard"))

        success = delete_patient(patient_id, db_path=db_path)
        if success:
            flash(f"Patient record for '{existing['full_name']}' was deleted successfully.", "success")
        else:
            flash("Error deleting patient record from database.", "danger")

        return redirect(url_for("dashboard"))

    # ------------------ Error Handlers ------------------

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("500.html"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Security validation (CSRF token) failed or expired. Please reload and try again.", "danger")
        return redirect(url_for("dashboard"))

    return app


# Root application instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "0").strip() in ("1", "true", "True")
    print(f"Starting VitalSense AI on http://127.0.0.1:{port} (Debug: {debug})")
    app.run(host="127.0.0.1", port=port, debug=debug)
