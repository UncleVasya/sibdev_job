import datetime
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Deal:
    """Представление сделки, которое удобно использовать в тестах."""
    customer: str
    gem: str
    total: Decimal
    quantity: int
    date: datetime.datetime

    def to_list(self):
        return [self.customer, self.gem, self.total, self.quantity, self.date]