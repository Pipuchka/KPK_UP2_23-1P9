import datetime
from peewee import *
from playhouse import validate_one_of, validate_length

db = SqliteDatabase('employee_status.db')

def validate_positive_or_none(value):
    if value is not None and value <= 0:
        raise ValueError("Значение должно быть положительным или None")

def validate_future_or_none(value):
    if value is not None and value < datetime.date.today():
        raise ValueError("Дата не может быть в прошлом")

def validate_hire_date(value):
    if value < datetime.date(1900, 1, 1):
        raise ValueError("Дата найма не может быть раньше 1900-01-01")
    if value > datetime.date.today():
        raise ValueError("Дата найма не может быть позже сегодняшнего дня")

def validate_load_factor(value):
    if not (0 < value <= 2.0):
        raise ValueError("Ставка должна быть в диапазоне (0, 2.0]")

class BaseModel(Model):
    class Meta:
        database = db

class Employee(BaseModel):
    """Минимальная информация о сотруднике – только ссылка на профиль и статус"""
    class Meta:
        db_table = "employees"
    
    id = AutoField()
    user_id = IntegerField(unique=True, null=False, validators=[validate_positive_or_none])
    hire_date = DateField(null=False, validators=[validate_hire_date])
    status = CharField(max_length=20, default='active', 
                      validators=[validate_one_of(['active', 'on_vacation', 'sick_leave', 'fired'])])
    is_deleted = BooleanField(default=False)

class Position(BaseModel):
    class Meta:
        db_table = "positions"
    
    id = AutoField()
    title = CharField(max_length=100, null=False, validators=[validate_length(1, 100)])
    description = TextField(null=True)

class EmployeePosition(BaseModel):
    class Meta:
        db_table = "employee_positions"
    
    id = AutoField()
    employee_id = ForeignKeyField(Employee, backref='positions', on_delete='CASCADE', null=False)
    position_id = ForeignKeyField(Position, backref='employees', on_delete='CASCADE', null=False)
    start_date = DateField(null=False, validators=[validate_future_or_none])
    end_date = DateField(null=True, validators=[validate_future_or_none])
    load_factor = FloatField(null=False, validators=[validate_load_factor])

class Vacation(BaseModel):
    class Meta:
        db_table = "vacations"
    
    id = AutoField()
    employee_id = ForeignKeyField(Employee, backref='vacations', on_delete='CASCADE', null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    type = CharField(max_length=50, null=False, validators=[validate_length(1, 50)])

class SickLeave(BaseModel):
    class Meta:
        db_table = "sick_leaves"
    
    id = AutoField()
    employee_id = ForeignKeyField(Employee, backref='sick_leaves', on_delete='CASCADE', null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    diagnosis = TextField(null=True, validators=[validate_length(0, 500)])

def initialize_db():
    db.connect()
    db.create_tables([Employee, Position, EmployeePosition, Vacation, SickLeave], safe=True)
    db.close()