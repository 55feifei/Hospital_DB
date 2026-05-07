# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Chinese university database course project: a hospital outpatient appointment management system. The grading rubric drives the architecture — every requirement (≥5 tables with referential integrity, ≥3 triggers, ≥2 parameterized procedures, ≥2 cursor procedures, ≥2 secondary indexes with EXPLAIN analysis, GUI, normalization to 3NF) maps to a specific file. **Don't remove or simplify features that look redundant — they exist to satisfy a grading point.** See `README.md` "评分点速查" for the mapping.

## Stack

Python 3.9+ · PyMySQL · PyQt5 · MySQL 8.0+ (InnoDB). Three-tier: `dao/` → `service/` → `ui/`.

## Common commands

The local Python env on this Windows machine sometimes lives at `.conda/python.exe` (project-local conda) and sometimes at the system Python. Pick whichever is present. The MySQL client is at `C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe`.

```powershell
# Initialize / reset DB (run in order)
mysql -uroot -p --default-character-set=utf8mb4 hospital_db < sql/01_schema.sql
mysql -uroot -p --default-character-set=utf8mb4 hospital_db < sql/02_triggers.sql
mysql -uroot -p --default-character-set=utf8mb4 hospital_db < sql/03_procedures.sql
mysql -uroot -p --default-character-set=utf8mb4 hospital_db < sql/04_views.sql
mysql -uroot -p --default-character-set=utf8mb4 hospital_db < sql/05_init_data.sql
mysql -uroot -p --default-character-set=utf8mb4 hospital_db < sql/06_security.sql

# Launch GUI
python src/main.py

# Run all tests
python -m unittest discover tests -v

# Run a single test file / case
python -m unittest tests.test_appointment -v
python -m unittest tests.test_appointment.TestProcedureBook.test_book_success -v
```

**Always pass `--default-character-set=utf8mb4` when invoking `mysql` from the command line on Windows.** The default cmd-line charset is gbk, which mangles the Chinese ENUM literals (`'已预约'`, `'已取消'`, etc.) and silently produces (a) "Incorrect string value" errors on stored-procedure OUT params, (b) UPDATEs that match 0 rows because the literal doesn't equal the stored value. This bit us when applying `hotfix_appt_no_release.sql`.

Default seed accounts: `admin` / `doc001` / `pat001` — all password `123456`.

## Database connection config

`src/config.py` holds the root password (`DB_CONFIG`) and a least-privilege app account (`DB_CONFIG_APP` → `hospital_app`/`App@2026` created by `06_security.sql`). The security tests in `test_concurrency_security.py` connect as `hospital_app` to verify it cannot run DDL.

## Architecture — what to know before editing

### State machine for `appointment.status`
`已预约 → 已就诊 / 已取消 / 爽约`. The status transitions are enforced in *three* places that must stay in sync:

1. **Trigger `trg_appt_after_update`** (sql/02_triggers.sql) — restores `schedule.remaining_quota` on cancel; auto-creates `medical_record` on visit.
2. **Procedure `sp_cancel_appointment`** — sets `status='已取消'`, **clears `appt_no=NULL` to release the queue number**, and refunds `payment` only if it was `已支付`.
3. **Procedure `sp_book_appointment`** — uses `SELECT ... FOR UPDATE` for row-level locking (concurrency safety), and computes the next `appt_no` as `MAX(appt_no)+1 WHERE status IN ('已预约','已就诊')` so released numbers from cancelled appointments are reused.

### `appt_no` is nullable on purpose
`appointment.appt_no` is `INT NULL` (not `NOT NULL`) with `UNIQUE(schedule_id, appt_no)`. MySQL allows multiple NULLs in a unique index — this is what enables seat-number recycling after cancel/no-show. If you re-create the schema from `01_schema.sql`, this is already encoded; if you only re-deploy procedures, also re-apply `sql/hotfix_appt_no_release.sql`.

### `Database.call_proc` parameter convention
`PyMySQL.callproc` maps **all** parameters (IN + OUT) to session vars `@_<proc>_<i>` in original declaration order. So `Database.call_proc("sp_book_appointment", (pid, sid, 0, ""))` returns `out = [pid, sid, appt_id, msg]` — the OUT values are at indices 2 and 3, *not* 0 and 1. See `src/service/appointment_service.py` for correct indexing for each procedure. This was a real bug source.

### Views are part of the public API
DAOs read from views, not raw tables, in several places:
- `v_patient_appointments` — used by `AppointmentDAO.search*`, `list_by_patient`, `list_all` (joins patient, schedule, doctor, department, payment in one place)
- `v_schedule_full` — used by `ScheduleDAO.list_available`, `search_for_patient`
- `v_doctor_workload` — used by `DoctorDAO.workload_view`

If you add a column referenced by code, add it to the relevant view in `04_views.sql` and re-deploy.

### Secondary indexes are non-FK-leading by design
Indexes in `01_schema.sql` (`idx_appt_patient_date`, `idx_schedule_date_remain`, `idx_payment_status_time`) are deliberately on non-foreign-key leading columns so that `tests/test_performance.py` can DROP and CREATE them to demonstrate EXPLAIN before/after. **Don't "consolidate" them with FK indexes** — doing so will break performance tests because MySQL rejects dropping an index that is needed to enforce a foreign key.

### UI layer conventions
- All three role panels (`patient_panel`, `doctor_panel`, `admin_panel`) use shared widgets from `src/ui/widgets.py`: `setup_table` (sortable + alternating rows), `NumericItem` (numeric sort that doesn't fall back to lexicographic), `make_status_item` (colored status badge), `search_field` (rounded clearable search input).
- Theme is centralized in `src/ui/theme.py` and applied once in `src/main.py` via `apply_theme(app)`. Don't put global colors inline in panel files.
- `src/main.py` sets `QT_QPA_PLATFORM_PLUGIN_PATH` from the PyQt5 install dir — required for conda envs on Windows where Qt can't auto-find `qwindows.dll`.
- Login flow validates the selected role *matches* `user.role` from the DB, even if the username/password are correct. Patient self-register goes through `RegisterDialog` (transactional INSERT into `patient` then `user_account`). Doctor account creation is bundled into `DoctorDialog(with_account=True)` from the admin panel.

## Test data scale

Seed data is small (~1k rows). `test_performance.py` inflates `appointment` to ~3k+ in its `setUpClass` to make EXPLAIN timing differences visible — this **mutates the dev database**. The schedule/appointment counts after running performance tests are typically schedule≈6k, appointment≈11k. To reset, re-run `05_init_data.sql` (or `99_drop_all.sql` then full setup).

## Hotfix-style schema changes

When the live DB has accumulated data and the schema needs a tweak (e.g. the `appt_no` nullability change), prefer writing a `sql/hotfix_*.sql` that is idempotent and applies both DDL and data backfill in one file, rather than asking users to re-run `01_schema.sql` (which `DROP DATABASE`s everything). Apply with `mysql --default-character-set=utf8mb4 hospital_db < sql/hotfix_*.sql`. Update `01_schema.sql` and `03_procedures.sql` in the same change so a fresh setup matches.
