from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Listing:
    """Модель данных для одного объявления Avito."""
    url: str
    title: str
    price: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    
    # Дополнительные поля из урока
    bail: Optional[str] = None      # Залог
    tax: Optional[str] = None       # Комиссия
    services: Optional[str] = None  # ЖКУ
