from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class VehicleCreateDTO:
    brand: str
    model: str
    year: int
    plate: str
    vin: Optional[str] = None
    color: Optional[str] = None
    engine_number: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None
    client_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class VehicleUpdateDTO:
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    plate: Optional[str] = None
    vin: Optional[str] = None
    color: Optional[str] = None
    engine_number: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None
    client_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class VehicleResponseDTO:
    id: str
    brand: str
    model: str
    year: int
    plate: str
    vin: Optional[str] = None
    color: Optional[str] = None
    engine_number: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None
    client_id: Optional[str] = None
    notes: Optional[str] = None
    full_name: str = ""
    display_name: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class VehicleListDTO:
    vehicles: List[VehicleResponseDTO]
    total: int
    skip: int = 0
    limit: int = 100
