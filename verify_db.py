#!/usr/bin/env python3
"""
Verify the generated ERP database with additional queries.
"""

import sqlite3
from datetime import datetime

def verify_database():
    """Run verification queries on the database."""
    conn = sqlite3.connect("erp_mock.db")
    cursor = conn.cursor()

    print("="*70)
    print("DATABASE VERIFICATION AND ADDITIONAL QUERIES")
    print("="*70)

    # Verify table schemas
    print("\n📋 TABLE SCHEMAS:\n")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table_name,) in tables:
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            pk_marker = " [PRIMARY KEY]" if pk else ""
            print(f"  - {name}: {type_}{pk_marker}")

    # Sample data from each table
    print("\n" + "="*70)
    print("SAMPLE DATA FROM EACH TABLE")
    print("="*70)

    # Production orders sample
    print("\n📦 PRODUCTION ORDERS (Sample - 5 rows):\n")
    cursor.execute("""
        SELECT order_id, part_name, material_type, quantity, status
        FROM production_orders
        ORDER BY scheduled_start DESC
        LIMIT 5
    """)
    print(f"{'Order ID':<20} {'Part Name':<25} {'Material':<10} {'Qty':<8} {'Status'}")
    print("-" * 85)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<25} {row[2]:<10} {row[3]:<8} {row[4]}")

    # Maintenance logs sample
    print("\n🔧 MAINTENANCE LOGS (Sample - 5 recent rows):\n")
    cursor.execute("""
        SELECT log_id, component_id, task_type, action_performed, result
        FROM maintenance_logs
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    print(f"{'Log ID':<20} {'Component':<15} {'Type':<12} {'Result':<15}")
    print("-" * 85)
    for row in cursor.fetchall():
        action_short = row[3][:30] + "..." if len(row[3]) > 33 else row[3]
        print(f"{row[0]:<20} {row[1]:<15} {row[2]:<12} {row[4]:<15}")

    # Material batches sample
    print("\n📊 MATERIAL BATCHES (Sample - 5 rows):\n")
    cursor.execute("""
        SELECT batch_id, material_type, supplier, quantity_kg, quality_grade
        FROM material_batches
        ORDER BY arrival_date DESC
        LIMIT 5
    """)
    print(f"{'Batch ID':<20} {'Material':<10} {'Supplier':<25} {'Quantity KG':<12} {'Grade'}")
    print("-" * 85)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<10} {row[2]:<25} {row[3]:>10.2f}  {row[4]}")

    # Advanced query: Component maintenance frequency
    print("\n" + "="*70)
    print("COMPONENT MAINTENANCE FREQUENCY ANALYSIS")
    print("="*70)
    print("\nMaintenance activities per component:\n")
    cursor.execute("""
        SELECT
            component_id,
            COUNT(*) as total_activities,
            SUM(CASE WHEN task_type = 'preventive' THEN 1 ELSE 0 END) as preventive,
            SUM(CASE WHEN task_type = 'corrective' THEN 1 ELSE 0 END) as corrective,
            SUM(CASE WHEN task_type = 'inspection' THEN 1 ELSE 0 END) as inspection,
            SUM(duration_minutes) as total_minutes
        FROM maintenance_logs
        GROUP BY component_id
        ORDER BY total_activities DESC
        LIMIT 10
    """)
    print(f"{'Component':<15} {'Total':<8} {'Prev':<6} {'Corr':<6} {'Insp':<6} {'Total Mins'}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<15} {row[1]:<8} {row[2]:<6} {row[3]:<6} {row[4]:<6} {row[5]}")

    # Advanced query: Production efficiency by material
    print("\n" + "="*70)
    print("PRODUCTION EFFICIENCY BY MATERIAL")
    print("="*70)
    print("\nOrder completion rates:\n")
    cursor.execute("""
        SELECT
            material_type,
            COUNT(*) as total_orders,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 1) as completion_rate
        FROM production_orders
        GROUP BY material_type
    """)
    print(f"{'Material':<10} {'Total':<8} {'Completed':<11} {'Delayed':<9} {'In Prog':<9} {'Rate %'}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<10} {row[1]:<8} {row[2]:<11} {row[3]:<9} {row[4]:<9} {row[5]}%")

    # Technician performance
    print("\n" + "="*70)
    print("TECHNICIAN PERFORMANCE SUMMARY")
    print("="*70)
    print("\nWork distribution:\n")
    cursor.execute("""
        SELECT
            technician_name,
            COUNT(*) as tasks_performed,
            SUM(duration_minutes) as total_minutes,
            ROUND(AVG(duration_minutes), 1) as avg_duration,
            SUM(CASE WHEN result = 'ok' THEN 1 ELSE 0 END) as successful_tasks
        FROM maintenance_logs
        GROUP BY technician_name
        ORDER BY tasks_performed DESC
    """)
    print(f"{'Technician':<20} {'Tasks':<8} {'Total Mins':<12} {'Avg Mins':<10} {'Success'}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<8} {row[2]:<12} {row[3]:<10} {row[4]}")

    # Join query: Orders with corresponding material batches
    print("\n" + "="*70)
    print("MATERIAL TRACEABILITY: ORDERS WITH BATCH CORRELATION")
    print("="*70)
    print("\nRecent orders with available material batches:\n")
    cursor.execute("""
        SELECT
            po.order_id,
            po.part_name,
            po.material_type,
            po.quantity,
            mb.batch_id,
            mb.lot_number,
            mb.quality_grade
        FROM production_orders po
        LEFT JOIN material_batches mb
            ON po.material_type = mb.material_type
            AND DATE(mb.arrival_date) <= DATE(po.scheduled_start)
        WHERE po.status = 'completed'
        ORDER BY po.scheduled_start DESC
        LIMIT 10
    """)
    print(f"{'Order ID':<20} {'Material':<10} {'Batch ID':<20} {'Lot Number':<20} {'Grade'}")
    print("-" * 85)
    for row in cursor.fetchall():
        batch = row[4] if row[4] else "N/A"
        lot = row[5] if row[5] else "N/A"
        grade = row[6] if row[6] else "N/A"
        print(f"{row[0]:<20} {row[2]:<10} {batch:<20} {lot:<20} {grade}")

    conn.close()
    print("\n" + "="*70)
    print("✅ Verification completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    verify_database()
