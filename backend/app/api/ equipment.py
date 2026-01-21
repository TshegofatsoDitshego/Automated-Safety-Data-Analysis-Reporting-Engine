"""
Equipment management API endpoints
CRUD operations for safety equipment registry
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.database import Equipment, EquipmentType, EquipmentStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class EquipmentCreate(BaseModel):
    """Schema for creating new equipment"""
    equipment_id: str
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_calibration_date: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "equipment_id": "GAS-001",
                "equipment_type": "gas_detector",
                "manufacturer": "MSA Safety",
                "model": "Altair 5X",
                "serial_number": "MSA-12345",
                "location": "Zone A - Production Floor",
                "metadata": {
                    "sensor_types": ["O2", "CO", "H2S", "LEL"],
                    "wireless": true
                }
            }
        }


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment"""
    equipment_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    last_calibration_date: Optional[datetime] = None
    next_calibration_due: Optional[datetime] = None
    metadata: Optional[dict] = None


class EquipmentResponse(BaseModel):
    """Schema for equipment responses"""
    equipment_id: str
    equipment_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    installation_date: datetime
    last_calibration_date: Optional[datetime]
    next_calibration_due: Optional[datetime]
    location: Optional[str]
    status: str
    metadata: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """
    Register new equipment in the system
    
    Creates a new equipment record that can start receiving sensor data
    """
    try:
        # Check if equipment_id already exists
        existing = db.query(Equipment).filter(
            Equipment.equipment_id == equipment.equipment_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Equipment with ID {equipment.equipment_id} already exists"
            )
        
        # Create new equipment
        new_equipment = Equipment(
            equipment_id=equipment.equipment_id,
            equipment_type=EquipmentType(equipment.equipment_type),
            manufacturer=equipment.manufacturer,
            model=equipment.model,
            serial_number=equipment.serial_number,
            location=equipment.location,
            installation_date=equipment.installation_date or datetime.utcnow(),
            last_calibration_date=equipment.last_calibration_date,
            metadata=equipment.metadata
        )
        
        db.add(new_equipment)
        db.commit()
        db.refresh(new_equipment)
        
        logger.info(f"Created equipment: {equipment.equipment_id}")
        
        return new_equipment
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid equipment type: {e}")
    except Exception as e:
        logger.error(f"Equipment creation error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[EquipmentResponse])
async def list_equipment(
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """
    List all equipment with optional filters
    
    Supports pagination and filtering by type, status, and location
    """
    try:
        query = db.query(Equipment)
        
        # Apply filters
        if equipment_type:
            query = query.filter(Equipment.equipment_type == EquipmentType(equipment_type))
        
        if status:
            query = query.filter(Equipment.status == EquipmentStatus(status))
        
        if location:
            query = query.filter(Equipment.location.ilike(f"%{location}%"))
        
        # Apply pagination
        equipment_list = query.offset(skip).limit(limit).all()
        
        return equipment_list
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {e}")
    except Exception as e:
        logger.error(f"Equipment list error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about specific equipment
    """
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(
            status_code=404,
            detail=f"Equipment {equipment_id} not found"
        )
    
    return equipment


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: str,
    updates: EquipmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update equipment information
    
    Allows partial updates - only specified fields are modified
    """
    try:
        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == equipment_id
        ).first()
        
        if not equipment:
            raise HTTPException(
                status_code=404,
                detail=f"Equipment {equipment_id} not found"
            )
        
        # Update only provided fields
        update_data = updates.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "equipment_type" and value:
                value = EquipmentType(value)
            elif field == "status" and value:
                value = EquipmentStatus(value)
            
            setattr(equipment, field, value)
        
        db.commit()
        db.refresh(equipment)
        
        logger.info(f"Updated equipment: {equipment_id}")
        
        return equipment
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {e}")
    except Exception as e:
        logger.error(f"Equipment update error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete equipment from the system
    
    WARNING: This will cascade delete all associated sensor readings and alerts
    """
    try:
        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == equipment_id
        ).first()
        
        if not equipment:
            raise HTTPException(
                status_code=404,
                detail=f"Equipment {equipment_id} not found"
            )
        
        db.delete(equipment)
        db.commit()
        
        logger.info(f"Deleted equipment: {equipment_id}")
        
        return {"message": f"Equipment {equipment_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Equipment deletion error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{equipment_id}/health")
async def get_equipment_health(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get equipment health summary
    
    Returns aggregated statistics and health indicators
    """
    try:
        from sqlalchemy import text, func
        from datetime import timedelta
        
        # Check equipment exists
        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == equipment_id
        ).first()
        
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        
        # Get reading statistics from last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        query = text("""
            SELECT 
                COUNT(DISTINCT DATE(time)) as active_days,
                COUNT(*) as total_readings,
                COUNT(DISTINCT metric_name) as metrics_count,
                MAX(time) as last_reading,
                SUM(CASE WHEN reading_status = 'critical' THEN 1 ELSE 0 END) as critical_readings
            FROM sensor_readings
            WHERE equipment_id = :equipment_id
              AND time > :cutoff
        """)
        
        result = db.execute(query, {"equipment_id": equipment_id, "cutoff": cutoff}).first()
        
        # Get recent alert count
        from app.models.database import Alert
        alert_count = db.query(func.count(Alert.alert_id)).filter(
            Alert.equipment_id == equipment_id,
            Alert.triggered_at > cutoff
        ).scalar()
        
        # Calculate health score (0-100)
        health_score = 100
        if result.active_days < 25:  # should be active most days
            health_score -= 20
        if result.critical_readings > 100:
            health_score -= 30
        if alert_count > 10:
            health_score -= 20
        if equipment.status != EquipmentStatus.ACTIVE:
            health_score -= 30
        
        health_score = max(0, health_score)
        
        return {
            "equipment_id": equipment_id,
            "health_score": health_score,
            "status": equipment.status.value,
            "active_days_last_30": result.active_days,
            "total_readings_last_30": result.total_readings,
            "metrics_tracked": result.metrics_count,
            "last_reading_time": result.last_reading,
            "critical_readings_last_30": result.critical_readings,
            "alerts_last_30": alert_count,
            "days_since_calibration": (
                (datetime.utcnow() - equipment.last_calibration_date).days
                if equipment.last_calibration_date else None
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Equipment health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))