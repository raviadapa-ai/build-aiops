import os
import time
import sqlite3
from datetime import datetime
import psutil

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "metrics.db")


def create_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cpu_percent REAL,
        memory_percent REAL,
        disk_percent REAL,
        bytes_sent INTEGER,
        bytes_recv INTEGER,
        process_count INTEGER,
        system_load REAL
    )
    """)

    connection.commit()
    connection.close()


def collect_metrics():
    net_io = psutil.net_io_counters()

    try:
        system_load = os.getloadavg()[0]
    except AttributeError:
        system_load = psutil.cpu_percent(interval=1)

    metrics = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "process_count": len(psutil.pids()),
        "system_load": system_load
    }

    return metrics

def save_metrics(metrics):

    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO system_metrics (
        timestamp,
        cpu_percent,
        memory_percent,
        disk_percent,
        bytes_sent,
        bytes_recv,
        process_count,
        system_load      
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics["timestamp"],
        metrics["cpu_percent"],
        metrics["memory_percent"],
        metrics["disk_percent"],
        metrics["bytes_sent"],
        metrics["bytes_recv"],
        metrics["process_count"],
        metrics["system_load"]
    ))

    connection.commit()
    connection.close()


def print_metrics(metrics):
    print("-" * 70)
    print(f"Timestamp           : {metrics['timestamp']}")
    print(f"CPU Usage           : {metrics['cpu_percent']}%")
    print(f"Memory Usage        : {metrics['memory_percent']}%")
    print(f"Disk Usage          : {metrics['disk_percent']}%")
    print(f"Network Bytes Sent  : {metrics['bytes_sent']}")
    print(f"Network Bytes Recv  : {metrics['bytes_recv']}")
    print(f"Process Count       : {metrics['process_count']}")
    print(f"System Load         : {metrics['system_load']}")
    
def run_collector(interval_seconds=5):
    initialize_database()

    print("AIOps Metrics Collection Pipeline Started")
    print(f"Saving metrics to: {DB_PATH}")
    print("Press CTRL + C to stop")

    try:
        while True:
            metrics = collect_metrics()
            save_metrics(metrics)
            print_metrics(metrics)
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nMetrics collector stopped.")


if __name__ == "__main__":
    run_collector(interval_seconds=5)