from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from database import get_db, init_db, Place

# Initialize FastAPI
app = FastAPI(
    title="Safe Zone Database API",
    description="A secure database backend server",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class PlaceCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: str


class PlaceUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None


class PlaceResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Server is running"}


# ==================== PLACE ENDPOINTS ====================

@app.post("/api/places", response_model=PlaceResponse)
def create_place(place: PlaceCreate, db: Session = Depends(get_db)):
    """Create a new place"""
    db_place = Place(
        name=place.name,
        latitude=place.latitude,
        longitude=place.longitude,
        address=place.address
    )
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    
    return db_place


@app.get("/api/places/{place_id}", response_model=PlaceResponse)
def get_place(place_id: int, db: Session = Depends(get_db)):
    """Get a specific place by ID"""
    place = db.query(Place).filter(Place.id == place_id).first()
    
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    return place


@app.get("/api/places", response_model=List[PlaceResponse])
def list_places(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all places with pagination"""
    places = db.query(Place).offset(skip).limit(limit).all()
    return places


@app.put("/api/places/{place_id}", response_model=PlaceResponse)
def update_place(
    place_id: int,
    place_update: PlaceUpdate,
    db: Session = Depends(get_db)
):
    """Update a place"""
    db_place = db.query(Place).filter(Place.id == place_id).first()
    
    if not db_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    if place_update.name:
        db_place.name = place_update.name
    if place_update.latitude is not None:
        db_place.latitude = place_update.latitude
    if place_update.longitude is not None:
        db_place.longitude = place_update.longitude
    if place_update.address:
        db_place.address = place_update.address
    
    db_place.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_place)
    
    return db_place


@app.delete("/api/places/{place_id}")
def delete_place(place_id: int, db: Session = Depends(get_db)):
    """Delete a place"""
    db_place = db.query(Place).filter(Place.id == place_id).first()
    
    if not db_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    
    db.delete(db_place)
    db.commit()
    
    return {"message": "Place deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
