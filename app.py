from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///safe_zone.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Place(db.Model):
    __tablename__ = 'places'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Create tables
with app.app_context():
    db.create_all()


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200


# ==================== PLACE ENDPOINTS ====================


# Serve the single-page HTML UI
@app.route('/', methods=["GET"])
def index():
    return render_template('index.html')

@app.route('/api/places', methods=['POST'])
def create_place():
    """Create a new place"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not all(k in data for k in ['name', 'latitude', 'longitude', 'address']):
            return jsonify({"error": "Missing required fields"}), 400
        
        place = Place(
            name=data['name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            address=data['address']
        )
        db.session.add(place)
        db.session.commit()
        
        return jsonify(place.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/places/<int:place_id>', methods=['GET'])
def get_place(place_id):
    """Get a specific place by ID"""
    place = Place.query.filter_by(id=place_id).first()
    
    if not place:
        return jsonify({"error": "Place not found"}), 404
    
    return jsonify(place.to_dict()), 200


@app.route('/api/places', methods=['GET'])
def list_places():
    """List all places with pagination"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    places = Place.query.offset(skip).limit(limit).all()
    return jsonify([place.to_dict() for place in places]), 200


@app.route('/api/places/<int:place_id>', methods=['PUT'])
def update_place(place_id):
    """Update a place"""
    try:
        place = Place.query.filter_by(id=place_id).first()
        
        if not place:
            return jsonify({"error": "Place not found"}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            place.name = data['name']
        if 'latitude' in data:
            place.latitude = data['latitude']
        if 'longitude' in data:
            place.longitude = data['longitude']
        if 'address' in data:
            place.address = data['address']
        
        place.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(place.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/places/<int:place_id>', methods=['DELETE'])
def delete_place(place_id):
    """Delete a place"""
    try:
        place = Place.query.filter_by(id=place_id).first()
        
        if not place:
            return jsonify({"error": "Place not found"}), 404
        
        db.session.delete(place)
        db.session.commit()
        
        return jsonify({"message": "Place deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)), debug=os.getenv('DEBUG', 'False') == 'True')
