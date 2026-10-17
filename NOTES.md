# Notes: SQLAlchemy `relationship` vs `ForeignKey`

## Two different layers

- **`ForeignKey("plants.id")`** — a real database-level constraint. It
  lives in the actual SQL table (`sensor_reading.plant_id` points at
  `plants.id`). This is what SQLite/SQL enforces.
- **`relationship(...)`** — a Python-only convenience. It does not create
  a column. It lets you navigate between linked objects in memory without
  writing a manual query.

```python
class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(primary_key=True)
    readings: Mapped[list["SensorReading"]] = relationship(back_populates="plant")

class SensorReading(Base):
    __tablename__ = "sensor_reading"
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    plant: Mapped["Plant"] = relationship(back_populates="readings")
```

## `back_populates` is a cross-reference, not a column name

Each `relationship()` call's `back_populates` string names the **attribute**
(not the class, not a column) on the *other* class that points back to it:

- `Plant.readings` → `back_populates="plant"` → means "my partner attribute
  is called `plant`, defined on `SensorReading`."
- `SensorReading.plant` → `back_populates="readings"` → means "my partner
  attribute is called `readings`, defined on `Plant`."

Vocabulary:
- **Class name**: `Plant` (after `class`)
- **Attribute name**: `id`, `name`, `readings`, `plant` (left of `:` in the
  class body) — accessed with a dot, e.g. `fern.readings`
- **Column name**: only applies to attributes backed by `mapped_column(...)`
  (e.g. `id`, `name`). `readings` and `plant` are NOT columns — they only
  exist in Python, built on top of the `plant_id` foreign key column.

## Why it's useful

Without `relationship`, getting a plant's readings means a manual query:

```python
session.scalars(select(SensorReading).where(SensorReading.plant_id == fern.id)).all()
```

With `relationship`, it's just attribute access:

```python
fern.readings        # list[SensorReading]
some_reading.plant   # Plant
```

Setting one side automatically keeps the other side in sync in memory
(that's the "back" in `back_populates`):

```python
r1.plant = fern   # also adds r1 into fern.readings automatically
```
