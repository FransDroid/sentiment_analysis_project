import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_sent: int
    network_recv: int

class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history = []
        self.start_time = time.time()
        self.processing_times = []

    def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage=disk.percent,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv
            )
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return None

    def log_processing_time(self, operation: str, start_time: float, end_time: float):
        """Log processing time for an operation"""
        duration = end_time - start_time
        self.processing_times.append({
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now()
        })

        # Keep only last 100 measurements
        if len(self.processing_times) > 100:
            self.processing_times = self.processing_times[-100:]

        self.logger.info(f"{operation} completed in {duration:.2f} seconds")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        current_metrics = self.get_system_metrics()
        uptime = time.time() - self.start_time

        # Calculate average processing times
        avg_times = {}
        for record in self.processing_times:
            operation = record['operation']
            if operation not in avg_times:
                avg_times[operation] = []
            avg_times[operation].append(record['duration'])

        for operation in avg_times:
            avg_times[operation] = sum(avg_times[operation]) / len(avg_times[operation])

        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'current_metrics': {
                'cpu_percent': current_metrics.cpu_percent if current_metrics else 0,
                'memory_percent': current_metrics.memory_percent if current_metrics else 0,
                'disk_usage': current_metrics.disk_usage if current_metrics else 0
            },
            'average_processing_times': avg_times,
            'total_operations': len(self.processing_times)
        }

    def check_system_health(self) -> Dict[str, Any]:
        """Check system health and return status"""
        metrics = self.get_system_metrics()

        if not metrics:
            return {'status': 'error', 'message': 'Unable to get system metrics'}

        issues = []
        warnings = []

        # Check CPU usage
        if metrics.cpu_percent > 90:
            issues.append(f"High CPU usage: {metrics.cpu_percent}%")
        elif metrics.cpu_percent > 75:
            warnings.append(f"Elevated CPU usage: {metrics.cpu_percent}%")

        # Check memory usage
        if metrics.memory_percent > 90:
            issues.append(f"High memory usage: {metrics.memory_percent}%")
        elif metrics.memory_percent > 75:
            warnings.append(f"Elevated memory usage: {metrics.memory_percent}%")

        # Check disk usage
        if metrics.disk_usage > 95:
            issues.append(f"High disk usage: {metrics.disk_usage}%")
        elif metrics.disk_usage > 85:
            warnings.append(f"Elevated disk usage: {metrics.disk_usage}%")

        if issues:
            status = 'critical'
            message = 'System has critical issues'
        elif warnings:
            status = 'warning'
            message = 'System has performance warnings'
        else:
            status = 'healthy'
            message = 'System is running normally'

        return {
            'status': status,
            'message': message,
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics.__dict__
        }

class ProcessingTimer:
    """Context manager for timing operations"""
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        self.monitor.log_processing_time(self.operation_name, self.start_time, end_time)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()