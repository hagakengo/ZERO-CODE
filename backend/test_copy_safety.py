import tempfile
from pathlib import Path
import unittest
import test_startup_safety

class CopySafetyTests(unittest.TestCase):
    run_python = test_startup_safety.StartupSafetyTests.run_python

    def test_explicit_setup_copy_preserves_values_and_refuses_nonempty(self):
        with tempfile.TemporaryDirectory() as folder:
            self.run_python(Path(folder) / 'source.db', """
from app.main import seed, engine
from sqlalchemy import create_engine, text, MetaData, select
from migrate_sqlite_to_postgres import copy_data, TABLES
from app.main import Base
seed()
with engine.begin() as db:
    db.execute(text('UPDATE daily_metrics SET day=999, level=999, xp=999'))
target = create_engine(str(engine.url).replace('source.db', 'target.db'))
try:
    copy_data(engine, target)
    raise AssertionError('Unprepared target must fail')
except RuntimeError:
    pass
Base.metadata.create_all(target) # explicitly prepared disposable test DB
# Fail after missions insertion; transaction must roll back all inserted rows.
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
def fail_later(conn, cursor, statement, parameters, context, executemany):
    if statement.startswith('INSERT INTO daily_metrics'):
        raise RuntimeError('injected interruption')
event.listen(target, 'before_cursor_execute', fail_later)
try:
    copy_data(engine, target)
    raise AssertionError('Expected interruption')
except RuntimeError:
    pass
finally:
    event.remove(target, 'before_cursor_execute', fail_later)
with target.connect() as conn:
    assert conn.scalar(text('SELECT COUNT(*) FROM missions')) == 0
copy_data(engine, target)
for name in TABLES:
    meta = MetaData()
    meta.reflect(bind=engine)
    with engine.connect() as source, target.connect() as dest:
        table = meta.tables[name]
        assert list(source.execute(select(table))) == list(dest.execute(select(table)))
try:
    copy_data(engine, target)
    raise AssertionError('Nonempty target must fail')
except RuntimeError:
    pass
""")
