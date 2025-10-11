#!/usr/bin/env python3
"""
Social Media Sentiment Analysis Dashboard
Main application entry point
"""

import os
import sys
import argparse
import signal
import threading
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.logger import setup_logging, get_logger
from src.utils.error_handler import error_handler
from src.utils.monitoring import performance_monitor, ProcessingTimer
from src.streaming.real_time_pipeline import RealTimePipeline
from src.dashboard.app import app
from config.settings import Config

class SentimentAnalysisApp:
    def __init__(self):
        self.logger = setup_logging()
        self.pipeline = None
        self.dashboard_thread = None
        self.pipeline_thread = None
        self.is_running = False

    def run_dashboard_only(self):
        """Run only the web dashboard"""
        self.logger.info(f"Starting dashboard in standalone mode on port {Config.FLASK_PORT}...")

        try:
            app.run(
                debug=Config.FLASK_DEBUG,
                host='0.0.0.0',
                port=Config.FLASK_PORT,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            error_handler.handle_processing_error("dashboard_startup", e)

    def run_pipeline_only(self):
        """Run only the data collection pipeline"""
        self.logger.info("Starting data collection pipeline...")

        try:
            self.pipeline = RealTimePipeline()
            self.pipeline.start_streaming()
        except KeyboardInterrupt:
            self.logger.info("Pipeline stopped by user")
        except Exception as e:
            self.logger.error(f"Error running pipeline: {e}")
            error_handler.handle_processing_error("pipeline_startup", e)
        finally:
            if self.pipeline:
                self.pipeline.stop_streaming()

    def run_full_system(self):
        """Run both pipeline and dashboard"""
        self.logger.info("Starting full sentiment analysis system...")
        self.is_running = True

        try:
            # Start dashboard in separate thread
            self.dashboard_thread = threading.Thread(
                target=self._run_dashboard_thread,
                daemon=True
            )
            self.dashboard_thread.start()
            self.logger.info(f"Dashboard started on http://localhost:{Config.FLASK_PORT}")

            # Start pipeline in separate thread
            self.pipeline_thread = threading.Thread(
                target=self._run_pipeline_thread,
                daemon=True
            )
            self.pipeline_thread.start()
            self.logger.info("Data collection pipeline started")

            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Main monitoring loop
            self._monitoring_loop()

        except Exception as e:
            self.logger.error(f"Error in full system: {e}")
            error_handler.handle_processing_error("full_system", e)
        finally:
            self.stop_system()

    def _run_dashboard_thread(self):
        """Run dashboard in thread"""
        try:
            app.run(
                debug=False,  # Disable debug in threaded mode
                host='0.0.0.0',
                port=Config.FLASK_PORT,
                threaded=True,
                use_reloader=False
            )
        except Exception as e:
            self.logger.error(f"Dashboard thread error: {e}")

    def _run_pipeline_thread(self):
        """Run pipeline in thread"""
        try:
            self.pipeline = RealTimePipeline()
            self.pipeline.start_streaming()
        except Exception as e:
            self.logger.error(f"Pipeline thread error: {e}")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("System monitoring started. Press Ctrl+C to stop.")

        try:
            while self.is_running:
                with ProcessingTimer(performance_monitor, "health_check"):
                    health = performance_monitor.check_system_health()

                    if health['status'] == 'critical':
                        self.logger.warning(f"System health critical: {health['message']}")
                        for issue in health['issues']:
                            self.logger.warning(f"  - {issue}")

                    elif health['status'] == 'warning':
                        self.logger.info(f"System health warning: {health['message']}")

                # Log performance summary every 5 minutes
                import time
                time.sleep(300)  # 5 minutes

                if self.is_running:
                    summary = performance_monitor.get_performance_summary()
                    self.logger.info(f"System uptime: {summary['uptime_formatted']}")
                    self.logger.info(f"Total operations: {summary['total_operations']}")

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_system()

    def stop_system(self):
        """Stop the entire system"""
        self.is_running = False

        if self.pipeline:
            self.logger.info("Stopping data collection pipeline...")
            self.pipeline.stop_streaming()

        self.logger.info("System shutdown complete")

    def show_status(self):
        """Show system status"""
        print("\n=== Sentiment Analysis System Status ===")

        # System health
        health = performance_monitor.check_system_health()
        print(f"System Health: {health['status'].upper()}")
        print(f"Message: {health['message']}")

        if health['warnings']:
            print("Warnings:")
            for warning in health['warnings']:
                print(f"  - {warning}")

        if health['issues']:
            print("Issues:")
            for issue in health['issues']:
                print(f"  - {issue}")

        # Performance summary
        summary = performance_monitor.get_performance_summary()
        print(f"\nUptime: {summary['uptime_formatted']}")
        print(f"Total Operations: {summary['total_operations']}")

        if summary['average_processing_times']:
            print("\nAverage Processing Times:")
            for operation, avg_time in summary['average_processing_times'].items():
                print(f"  {operation}: {avg_time:.2f}s")

        # Error summary
        errors = error_handler.get_error_summary()
        if errors:
            print("\nRecent Errors:")
            for error_key, error_info in errors.items():
                print(f"  {error_key}: {error_info['count']} occurrences")
        else:
            print("\nNo recent errors")

        print("\n" + "="*50 + "\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Social Media Sentiment Analysis Dashboard')
    parser.add_argument('--mode', choices=['dashboard', 'pipeline', 'full', 'status'],
                       default='full', help='Run mode (default: full)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')

    args = parser.parse_args()

    app_instance = SentimentAnalysisApp()

    if args.mode == 'dashboard':
        app_instance.run_dashboard_only()
    elif args.mode == 'pipeline':
        app_instance.run_pipeline_only()
    elif args.mode == 'full':
        app_instance.run_full_system()
    elif args.mode == 'status':
        app_instance.show_status()

if __name__ == '__main__':
    main()