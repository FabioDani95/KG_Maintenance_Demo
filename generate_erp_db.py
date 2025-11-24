#!/usr/bin/env python3
"""
Generate a SQLite database (erp_mock.db) for an injection molding manufacturing facility.
The database is consistent with the machine "IM-450T-ENGEL-2021-0721" from the existing Knowledge Graph.
"""

import sqlite3
from datetime import datetime, timedelta
import random
import os

# Configuration constants
MACHINE_ID = "IM-450T-ENGEL-2021-0721"
MOLD_ID = "MOLD_01"

# Component IDs from Knowledge Graph
COMPONENTS = [
    "SBA_01", "HS_01", "PMP_01", "VLV_SET_01", "OIL_01",
    "PF_01", "RF_01", "GB_01", "HX_01", "PRS_SET_01",
    "TMP_SET_01", "CM_01", "MOLD_01"
]

# Maintenance tasks from Knowledge Graph
MAINTENANCE_TASKS = {
    "DC001": {"component": "OIL_01", "action": "Check hydraulic oil level", "duration": 5, "type": "inspection"},
    "DC002": {"component": "HX_01", "action": "Check cooling water temperature", "duration": 3, "type": "inspection"},
    "DC003": {"component": "IM-450T-ENGEL-2021-0721", "action": "Visual inspection for leaks", "duration": 10, "type": "inspection"},
    "WC001": {"component": "GB_01", "action": "Lubricate tie bar bushings", "duration": 20, "type": "preventive"},
    "WC002": {"component": "HS_01", "action": "Inspect heater bands condition", "duration": 15, "type": "inspection"},
    "MC001": {"component": "PF_01", "action": "Replace hydraulic filters", "duration": 45, "type": "preventive"},
    "MC002": {"component": "PRS_SET_01", "action": "Calibrate pressure sensors", "duration": 60, "type": "preventive"},
    "MC003": {"component": "SBA_01", "action": "Inspect screw barrel wear", "duration": 30, "type": "inspection"},
}

# Corrective actions based on common issues
CORRECTIVE_ACTIONS = [
    {"component": "HS_01", "action": "Replace faulty heater band", "duration_range": (60, 120)},
    {"component": "VLV_SET_01", "action": "Fix hydraulic valve leak", "duration_range": (90, 180)},
    {"component": "PRS_SET_01", "action": "Replace pressure sensor", "duration_range": (30, 60)},
    {"component": "SBA_01", "action": "Clean screw and barrel", "duration_range": (120, 240)},
    {"component": "PMP_01", "action": "Adjust pump pressure settings", "duration_range": (20, 40)},
    {"component": "OIL_01", "action": "Top up hydraulic oil", "duration_range": (10, 20)},
    {"component": "PF_01", "action": "Emergency filter replacement", "duration_range": (30, 60)},
    {"component": "RF_01", "action": "Replace return filter", "duration_range": (25, 45)},
    {"component": "CM_01", "action": "Adjust clamping force", "duration_range": (15, 30)},
    {"component": "TMP_SET_01", "action": "Replace temperature sensor", "duration_range": (30, 50)},
]

# Italian technician names
TECHNICIANS = ["Mario Rossi", "Luca Bianchi", "Giovanni Ferrari", "Andrea Conti"]

# Part names and materials
PARTS = [
    {"name": "Casing_PP_V3", "material": "PP"},
    {"name": "Housing_ABS_T2", "material": "ABS"},
    {"name": "Cover_PP_Standard", "material": "PP"},
    {"name": "Bracket_ABS_Reinforced", "material": "ABS"},
]

# Material suppliers
SUPPLIERS = ["PlasticSupply_SPA", "PolymerItalia_SRL", "MaterialDirect_GmbH"]

# Storage locations
STORAGE_LOCATIONS = ["Warehouse_A", "Warehouse_B"]

# Quality grades
QUALITY_GRADES = ["A", "B"]

# Order statuses
ORDER_STATUSES = ["scheduled", "in_progress", "completed", "delayed"]

# Maintenance results
MAINTENANCE_RESULTS = ["ok", "component_replaced", "adjustment_made", "issue_found"]


def create_database(db_path="erp_mock.db"):
    """Create the SQLite database with three tables."""
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create production_orders table
    cursor.execute("""
        CREATE TABLE production_orders (
            order_id TEXT PRIMARY KEY,
            part_name TEXT NOT NULL,
            material_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            scheduled_start TEXT NOT NULL,
            scheduled_end TEXT NOT NULL,
            actual_start TEXT,
            actual_end TEXT,
            status TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            mold_id TEXT NOT NULL
        )
    """)

    # Create maintenance_logs table
    cursor.execute("""
        CREATE TABLE maintenance_logs (
            log_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            component_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            action_performed TEXT NOT NULL,
            technician_name TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            result TEXT NOT NULL,
            notes TEXT
        )
    """)

    # Create material_batches table
    cursor.execute("""
        CREATE TABLE material_batches (
            batch_id TEXT PRIMARY KEY,
            material_type TEXT NOT NULL,
            supplier TEXT NOT NULL,
            quantity_kg REAL NOT NULL,
            arrival_date TEXT NOT NULL,
            lot_number TEXT NOT NULL,
            quality_grade TEXT NOT NULL,
            storage_location TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


def is_working_hours(dt):
    """Check if datetime is within working hours (06:00-22:00, Monday-Friday)."""
    return dt.weekday() < 5 and 6 <= dt.hour < 22


def get_next_working_datetime(dt):
    """Get the next valid working datetime."""
    while not is_working_hours(dt):
        if dt.hour >= 22:
            # Move to next day at 6 AM
            dt = dt.replace(hour=6, minute=0, second=0) + timedelta(days=1)
        elif dt.hour < 6:
            # Move to 6 AM same day
            dt = dt.replace(hour=6, minute=0, second=0)
        else:
            # Weekend - move to Monday 6 AM
            days_ahead = 7 - dt.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            dt = dt.replace(hour=6, minute=0, second=0) + timedelta(days=days_ahead)
    return dt


def generate_production_orders(cursor, count=50):
    """Generate realistic production orders spanning last 3 months."""
    print(f"\nGenerating {count} production orders...")

    # Start from 3 months ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    orders = []
    for i in range(1, count + 1):
        # Random date within the range
        days_offset = random.randint(0, 89)
        order_date = start_date + timedelta(days=days_offset)

        # Select random part
        part = random.choice(PARTS)

        # Generate order ID
        order_id = f"ORD-{order_date.year}-{i:05d}"

        # Random quantity
        quantity = random.randint(500, 5000)

        # Calculate production time (rough estimate: 10-30 seconds per part)
        production_hours = (quantity * random.randint(10, 30)) / 3600

        # Schedule start time (within working hours)
        scheduled_start = get_next_working_datetime(
            order_date.replace(hour=random.randint(6, 18), minute=random.randint(0, 59))
        )

        # Schedule end time
        scheduled_end = scheduled_start + timedelta(hours=production_hours)
        scheduled_end = get_next_working_datetime(scheduled_end)

        # Determine status based on dates
        now = datetime.now()
        if scheduled_end < now - timedelta(days=1):
            # Completed orders (90% complete successfully, 10% delayed)
            status = "completed" if random.random() < 0.9 else "delayed"
            actual_start = scheduled_start + timedelta(minutes=random.randint(-30, 60))
            actual_end = scheduled_end + timedelta(minutes=random.randint(-60, 180))
        elif scheduled_start < now < scheduled_end:
            # In progress
            status = "in_progress"
            actual_start = scheduled_start + timedelta(minutes=random.randint(-30, 60))
            actual_end = None
        elif scheduled_start < now:
            # Should have started but might be delayed
            if random.random() < 0.15:  # 15% delayed
                status = "delayed"
                actual_start = None
                actual_end = None
            else:
                status = "in_progress"
                actual_start = scheduled_start + timedelta(minutes=random.randint(-30, 60))
                actual_end = None
        else:
            # Future orders
            status = "scheduled"
            actual_start = None
            actual_end = None

        orders.append((
            order_id,
            part["name"],
            part["material"],
            quantity,
            scheduled_start.isoformat(),
            scheduled_end.isoformat(),
            actual_start.isoformat() if actual_start else None,
            actual_end.isoformat() if actual_end else None,
            status,
            MACHINE_ID,
            MOLD_ID
        ))

    cursor.executemany("""
        INSERT INTO production_orders
        (order_id, part_name, material_type, quantity, scheduled_start, scheduled_end,
         actual_start, actual_end, status, machine_id, mold_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, orders)

    print(f"✓ Created {len(orders)} production orders")
    return len(orders)


def generate_maintenance_logs(cursor, count=120):
    """Generate realistic maintenance logs spanning last 6 months."""
    print(f"\nGenerating {count} maintenance log entries...")

    # Start from 6 months ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    logs = []
    log_counter = 1

    # Calculate daily, weekly, and monthly task occurrences
    daily_tasks = ["DC001", "DC002", "DC003"]
    weekly_tasks = ["WC001", "WC002"]
    monthly_tasks = ["MC001", "MC002", "MC003"]

    # Generate daily tasks (skip weekends)
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday-Friday
            for task_id in daily_tasks:
                task_info = MAINTENANCE_TASKS[task_id]

                # Random time during work hours
                log_time = current_date.replace(
                    hour=random.randint(6, 21),
                    minute=random.randint(0, 59)
                )

                log_id = f"MLOG-{log_time.year}-{log_counter:05d}"
                log_counter += 1

                # Determine component
                component = task_info["component"] if task_info["component"] != MACHINE_ID else random.choice(COMPONENTS)

                # Result (95% ok, 5% issues)
                if random.random() < 0.95:
                    result = "ok"
                    notes = f"Routine {task_info['action'].lower()} completed successfully"
                else:
                    result = "issue_found"
                    notes = f"Minor issue detected during {task_info['action'].lower()}, scheduled for follow-up"

                logs.append((
                    log_id,
                    log_time.isoformat(),
                    MACHINE_ID,
                    component,
                    task_info["type"],
                    task_info["action"],
                    random.choice(TECHNICIANS),
                    task_info["duration"],
                    result,
                    notes
                ))

        current_date += timedelta(days=1)

    # Generate weekly tasks (every Monday)
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 0:  # Monday
            for task_id in weekly_tasks:
                task_info = MAINTENANCE_TASKS[task_id]

                log_time = current_date.replace(
                    hour=random.randint(8, 14),
                    minute=random.randint(0, 59)
                )

                log_id = f"MLOG-{log_time.year}-{log_counter:05d}"
                log_counter += 1

                # Result (90% ok, 8% adjustment, 2% replacement)
                rand = random.random()
                if rand < 0.90:
                    result = "ok"
                    notes = f"{task_info['action']} completed, all parameters within specifications"
                elif rand < 0.98:
                    result = "adjustment_made"
                    notes = f"{task_info['action']} completed, minor adjustments made"
                else:
                    result = "component_replaced"
                    notes = f"{task_info['action']}: preventive component replacement performed"

                logs.append((
                    log_id,
                    log_time.isoformat(),
                    MACHINE_ID,
                    task_info["component"],
                    task_info["type"],
                    task_info["action"],
                    random.choice(TECHNICIANS),
                    task_info["duration"] + random.randint(-5, 10),
                    result,
                    notes
                ))

        current_date += timedelta(days=1)

    # Generate monthly tasks (first Monday of each month)
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 0 and current_date.day <= 7:  # First Monday
            for task_id in monthly_tasks:
                task_info = MAINTENANCE_TASKS[task_id]

                log_time = current_date.replace(
                    hour=random.randint(9, 12),
                    minute=random.randint(0, 59)
                )

                log_id = f"MLOG-{log_time.year}-{log_counter:05d}"
                log_counter += 1

                # Result (85% ok, 10% replacement, 5% adjustment)
                rand = random.random()
                if rand < 0.85:
                    result = "ok"
                    notes = f"{task_info['action']} completed, measurements within tolerance"
                elif rand < 0.95:
                    result = "component_replaced"
                    notes = f"{task_info['action']}: component replaced as part of preventive maintenance schedule"
                else:
                    result = "adjustment_made"
                    notes = f"{task_info['action']}: calibration adjustments made"

                logs.append((
                    log_id,
                    log_time.isoformat(),
                    MACHINE_ID,
                    task_info["component"],
                    task_info["type"],
                    task_info["action"],
                    random.choice(TECHNICIANS),
                    task_info["duration"] + random.randint(-10, 20),
                    result,
                    notes
                ))

        current_date += timedelta(days=1)

    # Generate corrective maintenance actions (random, less frequent)
    num_corrective = random.randint(15, 25)
    for _ in range(num_corrective):
        corrective = random.choice(CORRECTIVE_ACTIONS)

        # Random date
        days_offset = random.randint(0, 179)
        log_date = start_date + timedelta(days=days_offset)

        # During working hours
        log_time = get_next_working_datetime(
            log_date.replace(hour=random.randint(6, 20), minute=random.randint(0, 59))
        )

        log_id = f"MLOG-{log_time.year}-{log_counter:05d}"
        log_counter += 1

        duration = random.randint(*corrective["duration_range"])

        # Result (70% component replaced, 20% adjustment, 10% issue found but deferred)
        rand = random.random()
        if rand < 0.70:
            result = "component_replaced"
            notes = f"Corrective action: {corrective['action']}. Component replaced and tested successfully"
        elif rand < 0.90:
            result = "adjustment_made"
            notes = f"Corrective action: {corrective['action']}. System adjusted and returned to normal operation"
        else:
            result = "issue_found"
            notes = f"Corrective action: {corrective['action']}. Issue documented, spare parts ordered"

        logs.append((
            log_id,
            log_time.isoformat(),
            MACHINE_ID,
            corrective["component"],
            "corrective",
            corrective["action"],
            random.choice(TECHNICIANS),
            duration,
            result,
            notes
        ))

    # Limit to requested count and sort by timestamp
    logs.sort(key=lambda x: x[1])
    logs = logs[:count]

    cursor.executemany("""
        INSERT INTO maintenance_logs
        (log_id, timestamp, machine_id, component_id, task_type, action_performed,
         technician_name, duration_minutes, result, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, logs)

    print(f"✓ Created {len(logs)} maintenance log entries")
    return len(logs)


def generate_material_batches(cursor, count=30):
    """Generate realistic material batch records spanning last 4 months."""
    print(f"\nGenerating {count} material batch records...")

    # Start from 4 months ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)

    batches = []
    for i in range(1, count + 1):
        # Random arrival date
        days_offset = random.randint(0, 119)
        arrival_date = start_date + timedelta(days=days_offset)

        # Generate batch ID
        batch_id = f"MAT-{arrival_date.year}-{i:05d}"

        # Random material type
        material_type = random.choice(["PP", "ABS"])

        # Random supplier
        supplier = random.choice(SUPPLIERS)

        # Random quantity (500-2000 kg)
        quantity_kg = round(random.uniform(500, 2000), 2)

        # Generate lot number
        lot_number = f"LOT-{arrival_date.strftime('%Y%m%d')}-{random.randint(100, 999)}"

        # Random quality grade (80% A, 20% B)
        quality_grade = "A" if random.random() < 0.8 else "B"

        # Random storage location
        storage_location = random.choice(STORAGE_LOCATIONS)

        batches.append((
            batch_id,
            material_type,
            supplier,
            quantity_kg,
            arrival_date.date().isoformat(),
            lot_number,
            quality_grade,
            storage_location
        ))

    cursor.executemany("""
        INSERT INTO material_batches
        (batch_id, material_type, supplier, quantity_kg, arrival_date, lot_number,
         quality_grade, storage_location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, batches)

    print(f"✓ Created {len(batches)} material batch records")
    return len(batches)


def print_summary_statistics(conn):
    """Print summary statistics of the generated database."""
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("DATABASE SUMMARY STATISTICS")
    print("="*70)

    # Production orders statistics
    print("\n📦 PRODUCTION ORDERS:")
    cursor.execute("SELECT COUNT(*) FROM production_orders")
    print(f"   Total orders: {cursor.fetchone()[0]}")

    cursor.execute("SELECT status, COUNT(*) FROM production_orders GROUP BY status")
    for status, count in cursor.fetchall():
        print(f"   - {status}: {count}")

    cursor.execute("SELECT material_type, COUNT(*) FROM production_orders GROUP BY material_type")
    print("\n   Orders by material:")
    for material, count in cursor.fetchall():
        print(f"   - {material}: {count}")

    cursor.execute("SELECT SUM(quantity) FROM production_orders")
    total_parts = cursor.fetchone()[0]
    print(f"\n   Total parts produced/scheduled: {total_parts:,}")

    # Maintenance logs statistics
    print("\n🔧 MAINTENANCE LOGS:")
    cursor.execute("SELECT COUNT(*) FROM maintenance_logs")
    print(f"   Total log entries: {cursor.fetchone()[0]}")

    cursor.execute("SELECT task_type, COUNT(*) FROM maintenance_logs GROUP BY task_type")
    print("\n   Logs by type:")
    for task_type, count in cursor.fetchall():
        print(f"   - {task_type}: {count}")

    cursor.execute("SELECT result, COUNT(*) FROM maintenance_logs GROUP BY result")
    print("\n   Logs by result:")
    for result, count in cursor.fetchall():
        print(f"   - {result}: {count}")

    cursor.execute("SELECT technician_name, COUNT(*) FROM maintenance_logs GROUP BY technician_name")
    print("\n   Logs by technician:")
    for tech, count in cursor.fetchall():
        print(f"   - {tech}: {count}")

    cursor.execute("SELECT SUM(duration_minutes) FROM maintenance_logs")
    total_duration = cursor.fetchone()[0]
    print(f"\n   Total maintenance time: {total_duration:,} minutes ({total_duration/60:.1f} hours)")

    # Material batches statistics
    print("\n📊 MATERIAL BATCHES:")
    cursor.execute("SELECT COUNT(*) FROM material_batches")
    print(f"   Total batches: {cursor.fetchone()[0]}")

    cursor.execute("SELECT material_type, COUNT(*), SUM(quantity_kg) FROM material_batches GROUP BY material_type")
    print("\n   Batches by material:")
    for material, count, total_kg in cursor.fetchall():
        print(f"   - {material}: {count} batches, {total_kg:,.2f} kg")

    cursor.execute("SELECT supplier, COUNT(*) FROM material_batches GROUP BY supplier")
    print("\n   Batches by supplier:")
    for supplier, count in cursor.fetchall():
        print(f"   - {supplier}: {count}")

    cursor.execute("SELECT quality_grade, COUNT(*) FROM material_batches GROUP BY quality_grade")
    print("\n   Batches by quality grade:")
    for grade, count in cursor.fetchall():
        print(f"   - Grade {grade}: {count}")

    print("\n" + "="*70)


def demonstrate_queries(conn):
    """Demonstrate example queries with joins between tables."""
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("EXAMPLE QUERY: ORDERS WITH MAINTENANCE CORRELATION")
    print("="*70)
    print("\nFinding production orders and related maintenance activities:\n")

    query = """
    SELECT
        po.order_id,
        po.part_name,
        po.material_type,
        po.status,
        DATE(po.scheduled_start) as order_date,
        ml.log_id,
        ml.task_type,
        ml.action_performed,
        ml.result
    FROM production_orders po
    LEFT JOIN maintenance_logs ml
        ON DATE(po.scheduled_start) = DATE(ml.timestamp)
        AND ml.machine_id = po.machine_id
    WHERE po.status IN ('completed', 'in_progress')
    ORDER BY po.scheduled_start DESC
    LIMIT 10
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print(f"{'Order ID':<20} {'Part':<25} {'Status':<12} {'Maintenance':<15} {'Result':<15}")
    print("-" * 100)

    for row in results:
        order_id, part, material, status, order_date, log_id, task_type, action, result = row
        maint_info = f"{task_type or 'none'}" if task_type else "none"
        result_info = result or "-"
        print(f"{order_id:<20} {part:<25} {status:<12} {maint_info:<15} {result_info:<15}")

    print("\n" + "="*70)
    print("EXAMPLE QUERY: MATERIAL USAGE ANALYSIS")
    print("="*70)
    print("\nMaterial batch arrivals vs production orders:\n")

    query = """
    SELECT
        mb.material_type,
        COUNT(DISTINCT mb.batch_id) as batches_received,
        SUM(mb.quantity_kg) as total_kg_received,
        COUNT(DISTINCT po.order_id) as orders_placed,
        SUM(po.quantity) as total_parts_produced
    FROM material_batches mb
    LEFT JOIN production_orders po
        ON mb.material_type = po.material_type
    GROUP BY mb.material_type
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print(f"{'Material':<10} {'Batches':<10} {'Total KG':<15} {'Orders':<10} {'Parts':<15}")
    print("-" * 70)

    for row in results:
        material, batches, total_kg, orders, parts = row
        print(f"{material:<10} {batches:<10} {total_kg:>12,.2f}   {orders:<10} {parts:>12,}")

    print("\n" + "="*70)
    print("EXAMPLE QUERY: MAINTENANCE IMPACT ON PRODUCTION")
    print("="*70)
    print("\nCorrective maintenance events during production periods:\n")

    query = """
    SELECT
        ml.timestamp,
        ml.component_id,
        ml.action_performed,
        ml.duration_minutes,
        COUNT(po.order_id) as affected_orders
    FROM maintenance_logs ml
    LEFT JOIN production_orders po
        ON ml.machine_id = po.machine_id
        AND DATE(ml.timestamp) = DATE(po.scheduled_start)
        AND po.status IN ('in_progress', 'delayed')
    WHERE ml.task_type = 'corrective'
    GROUP BY ml.log_id
    ORDER BY ml.timestamp DESC
    LIMIT 10
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print(f"{'Date':<20} {'Component':<15} {'Action':<35} {'Duration':<10} {'Affected Orders'}")
    print("-" * 105)

    for row in results:
        timestamp, component, action, duration, affected = row
        date_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
        action_short = action[:32] + "..." if len(action) > 35 else action
        print(f"{date_str:<20} {component:<15} {action_short:<35} {duration:>3} min     {affected}")

    print("\n" + "="*70)


def main():
    """Main function to generate the ERP database."""
    print("="*70)
    print("GENERATING ERP MOCK DATABASE FOR INJECTION MOLDING FACILITY")
    print("="*70)
    print(f"\nMachine: {MACHINE_ID}")
    print(f"Mold: {MOLD_ID}")
    print(f"Database: erp_mock.db")

    # Create database and tables
    print("\nCreating database structure...")
    conn = create_database("erp_mock.db")
    print("✓ Database and tables created successfully")

    # Generate data
    generate_production_orders(conn.cursor(), count=50)
    generate_maintenance_logs(conn.cursor(), count=120)
    generate_material_batches(conn.cursor(), count=30)

    # Commit all changes
    conn.commit()

    # Print statistics
    print_summary_statistics(conn)

    # Demonstrate queries
    demonstrate_queries(conn)

    # Close connection
    conn.close()

    print("\n✅ Database generation completed successfully!")
    print(f"📁 Database file: erp_mock.db")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
