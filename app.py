import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from jinja2 import PackageLoader, Environment

# Initialize Flask app
app = Flask(__name__,
           static_folder="static",
           template_folder="templates")

# Set app configuration
app.config['TITLE'] = "ProcureIQ™ AI Procurement Automation System"
app.config['VERSION'] = "1.0.0"
app.secret_key = os.environ.get("SESSION_SECRET", "placeholder_secret")

# Configure database
from dotenv import load_dotenv
load_dotenv()

# Get the database URL from environment or use default for local development
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:naman@localhost:5432/INSOLU')

# Render uses postgres:// but SQLAlchemy requires postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import database models
from db_models import db

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Configure templates
# jinja_env = Environment(loader=PackageLoader('app', 'templates'))

# Root route
@app.route("/", methods=["GET"])
def root():
    return render_template(
        "dashboard.html",
        title="ProcureIQ Dashboard"
    )

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0"})

# Static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Import models
from models import RFQStatus, FileType
from db_models import RFQ, UploadedFile, ItemDetail, Vendor, Email
import uuid
import datetime
import os
from werkzeug.utils import secure_filename
from config import settings

# RFQ Routes
@app.route("/rfq/", methods=["GET"])
def get_rfq_dashboard():
    # Get all RFQs from database
    rfqs = RFQ.query.order_by(RFQ.created_at.desc()).all()   ## takin from database
    return render_template(
        "dashboard.html",
        title="RFQ Dashboard",
        rfqs=rfqs
    )

@app.route("/rfq/new", methods=["GET"])
def new_rfq_form():
    return render_template(
        "rfq_entry.html",
        title="New RFQ Entry"
    )

@app.route("/rfq/new", methods=["POST"])
def create_rfq():
    # Get form data
    client_name = request.form.get('client_name')
    notes = request.form.get('notes')
    files = request.files.getlist('files')

    # Generate RFQ number
    prefix = settings.RFQ_PREFIX
    year = settings.RFQ_YEAR

    # Get the latest RFQ number to increment
    last_rfq = RFQ.query.order_by(RFQ.rfq_number.desc()).first()
    if last_rfq and last_rfq.rfq_number.startswith(f"{prefix}-{year}-"):
        try:
            seq_num = int(last_rfq.rfq_number.split('-')[-1]) + 1
        except:
            seq_num = 1
    else:
        seq_num = 1

    rfq_number = f"{prefix}-{year}-{seq_num:05d}"

    # Create new RFQ
    new_rfq = RFQ(
        id=str(uuid.uuid4()),
        rfq_number=rfq_number,
        client_name=client_name,
        notes=notes,
        status=RFQStatus.DRAFT
    )

    # Add to database
    db.session.add(new_rfq)
    db.session.commit()

    # Process and save files
    if files:
        # Ensure upload directory exists
        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)

        for file in files:
            if file and file.filename:
                # Determine file type
                file_extension = file.filename.split('.')[-1].lower()
                if file_extension in ['pdf']:
                    file_type = FileType.PDF
                elif file_extension in ['docx', 'doc']:
                    file_type = FileType.DOCX
                elif file_extension in ['xlsx', 'xls']:
                    file_type = FileType.EXCEL
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                    file_type = FileType.IMAGE
                else:
                    continue  # Skip unsupported file types

                # Save file
                file_id = str(uuid.uuid4())
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, f"{file_id}_{filename}")
                file.save(file_path)

                # Create uploaded file record
                uploaded_file = UploadedFile(
                    id=file_id,
                    filename=filename,
                    file_type=file_type,
                    upload_date=datetime.datetime.utcnow(),
                    file_path=file_path,
                    rfq_id=new_rfq.id
                )

                db.session.add(uploaded_file)

        db.session.commit()

    return render_template(
        "data_extraction.html",
        title="Data Extraction",
        rfq=new_rfq,
        message=f"RFQ {rfq_number} created successfully"
    )

@app.route("/rfq/<rfq_id>", methods=["GET"])
def get_rfq_details(rfq_id):
    # Get RFQ from database
    rfq = RFQ.query.get_or_404(rfq_id)
    return render_template(
        "data_extraction.html",
        title=f"RFQ {rfq.rfq_number}",
        rfq=rfq
    )

@app.route("/rfq/<rfq_id>/process", methods=["POST"])
def process_rfq_documents(rfq_id):
    from services.document_processor import process_document
    import asyncio

    # Get RFQ from database
    rfq = RFQ.query.get_or_404(rfq_id)

    # Update status
    rfq.status = RFQStatus.PROCESSING
    db.session.commit()

    # Process documents
    items = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for file in rfq.files:
        try:
            # Process document asynchronously
            file_items = loop.run_until_complete(process_document(file.file_path, file.file_type))

            # Add items to database
            for item in file_items:
                db_item = ItemDetail(
                    id=item.id,
                    name=item.name,
                    quantity=item.quantity,
                    description=item.description,
                    rfq_id=rfq.id
                )
                db.session.add(db_item)
                items.append(db_item)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # Update RFQ status
    rfq.status = RFQStatus.READY
    db.session.commit()

    return jsonify({"status": "success", "items": [{"id": item.id, "name": item.name} for item in items]})

@app.route("/rfq/<rfq_id>/items", methods=["PUT"])
def update_rfq_items(rfq_id):
    # Get RFQ from database
    rfq = RFQ.query.get_or_404(rfq_id)

    # Get updated items from request
    items_data = request.get_json()

    if not items_data:
        print(f"Warning: No items data received in request")
        return jsonify({"status": "error", "message": "No items data provided"}), 400

    print(f"Received {len(items_data)} items to update for RFQ {rfq_id}")

    # Delete existing items
    ItemDetail.query.filter_by(rfq_id=rfq.id).delete()

    # Add new items
    for item_data in items_data:
        item = ItemDetail(
            id=item_data.get('id', str(uuid.uuid4())),
            name=item_data['name'],
            quantity=item_data.get('quantity'),
            description=item_data.get('description'),
            rfq_id=rfq.id
        )
        db.session.add(item)

    # Update RFQ
    rfq.updated_at = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({"status": "success", "message": f"Items updated successfully. Saved {len(items_data)} items."})

# Basic error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error=str(e), code=404), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error=str(e), code=500), 500

# Print startup message
print("Starting ProcureIQ AI Procurement Automation System...")

# Run the Flask application if this file is executed directly
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
