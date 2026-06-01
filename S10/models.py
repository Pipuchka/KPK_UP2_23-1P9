import datetime
from peewee import *
from playhouse import validate_one_of, validate_length

db = SqliteDatabase('employee_status.db')

# ---------- Валидаторы ----------
def validate_positive_or_none(value):
    if value is not None and value <= 0:
        raise ValueError("Значение должно быть положительным или None")

def validate_hire_date(value):
    """Только проверка на слишком раннюю дату (будущее разрешено)"""
    if value < datetime.date(1900, 1, 1):
        raise ValueError("Дата найма не может быть раньше 1900-01-01")
    # Убрана проверка на будущее

def validate_dates_start_end(start, end):
    """Вспомогательная функция для проверки end_date >= start_date"""
    if end is not None and end < start:
        raise ValueError("Дата окончания не может быть раньше даты начала")

# ---------- Модели ----------
class BaseModel(Model):
    class Meta:
        database = db

class Employee(BaseModel):
    class Meta:
        db_table = "employees"

    id = AutoField()
    user_id = IntegerField(unique=True, null=False, validators=[validate_positive_or_none])
    hire_date = DateField(null=False, validators=[validate_hire_date])
    status = CharField(max_length=20, default='active',
                      validators=[validate_one_of(['active', 'on_vacation', 'sick_leave', 'fired'])])
    is_deleted = BooleanField(default=False)
    updated_at = DateTimeField(default=datetime.datetime.now)  # новое поле

    def save(self, *args, **kwargs):
        """Автоматически обновляем updated_at при каждом сохранении"""
        self.updated_at = datetime.datetime.now()
        return super().save(*args, **kwargs)

    @property
    def positions(self):
        """Возвращает список должностей в формате, требуемом в doc.md"""
        result = []
        for ep in EmployeePosition.select().where(EmployeePosition.employee == self):
            result.append({
                "position_title": ep.position.title,
                "start_date": ep.start_date.isoformat(),
                "end_date": ep.end_date.isoformat() if ep.end_date else None,
                "load_factor": ep.load_factor
            })
        return result

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
    employee = ForeignKeyField(Employee, backref='employee_positions_rel', on_delete='CASCADE', null=False)
    position = ForeignKeyField(Position, backref='employee_positions_rel', on_delete='CASCADE', null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=True)
    load_factor = FloatField(null=False)

    def save(self, *args, **kwargs):
        # Проверка корректности дат (end_date >= start_date)
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("Дата окончания должности не может быть раньше даты начала")
        super().save(*args, **kwargs)

class Vacation(BaseModel):
    class Meta:
        db_table = "vacations"

    id = AutoField()
    employee = ForeignKeyField(Employee, backref='vacations', on_delete='CASCADE', null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    type = CharField(max_length=50, null=False, validators=[validate_length(1, 50)])
    is_deleted = BooleanField(default=False)  # мягкое удаление

    def save(self, *args, **kwargs):
        if self.end_date < self.start_date:
            raise ValueError("Дата окончания отпуска не может быть раньше даты начала")
        super().save(*args, **kwargs)

class SickLeave(BaseModel):
    class Meta:
        db_table = "sick_leaves"

    id = AutoField()
    employee = ForeignKeyField(Employee, backref='sick_leaves', on_delete='CASCADE', null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    diagnosis = TextField(null=True, validators=[validate_length(0, 500)])
    is_deleted = BooleanField(default=False)  # мягкое удаление

    def save(self, *args, **kwargs):
        if self.end_date < self.start_date:
            raise ValueError("Дата окончания больничного не может быть раньше даты начала")
        super().save(*args, **kwargs)

def initialize_db():
    db.connect()
    db.create_tables([Employee, Position, EmployeePosition, Vacation, SickLeave], safe=True)
    db.close()

if __name__ == '__main__':
    initialize_db()
    print("База данных инициализирована. Таблицы созданы.")