## Models configuration

Creating models is exactly the same as SQLAlchemy documentation. 

Using declarative approach:

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

bind = sa_manager.get_bind()

class MyModel(bind.model_declarative_base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
```

Or using the imperative approach:

```python
from dataclasses import dataclass
from sqlalchemy import Integer, String, Table, Column
@dataclass
class MyModel:
    id: int
    name: str

bind = sa_manager.get_bind()
    
imperative_table = Table(
    "imperative",
    bind.registry_mapper.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, primary_key=True),
)

bind.registry_mapper.map_imperatively(MyModel, imperative_table)

# or using the get_mapper() helper method
sa_manager.get_mapper().map_imperatively(MyModel, imperative_table)
```
