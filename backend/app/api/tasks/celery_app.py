"""
Celery application and background tasks
Handles scheduled analytics, report generation, and data processing
"""
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.core.database import get_db_context
from app.models.database import Equipment, Alert, AlertSeverity
from app.services.analytics import AnalyticsEngine

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "safety_analytics",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # restart worker after 50 tasks
)

# Scheduled tasks configuration
celery_app.conf.beat_schedule = {
    "run-anomaly-detection-hourly": {
        "task": "app.tasks.celery_app.detect_anomalies_all_equipment",
        "schedule": crontab(minute=0),  # every hour
    },
    "generate-daily-reports": {
        "task": "app.tasks.celery_app.generate_daily_reports",
        "schedule": crontab(hour=1, minute=0),  # 1 AM daily
    },
    "check-equipment-health": {
        "task": "app.tasks.celery_app.check_equipment_health_all",
        "schedule": crontab(hour="*/6"),  # every 6 hours
    },
    "cleanup-old-data": {
        "task": "app.tasks.celery_app.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # weekly Sunday 2 AM
    },
    "refresh-materialized-views": {
        "task": "app.tasks.celery_app.refresh_materialized_views",
        "schedule": crontab(minute="*/30"),  # every 30 minutes
    },
}


@celery_app.task(name="app.tasks.celery_app.detect_anomalies_all_equipment")
def detect_anomalies_all_equipment():
    """
    Run anomaly detection on all active equipment
    Generates alerts for detected anomalies
    """
    try:
        with get_db_context() as db:
            # Get all active equipment
            equipment_list = db.query(Equipment).filter(
                Equipment.status == "active"
            ).all()
            
            logger.info(f"Running anomaly detection for {len(equipment_list)} equipment")
            
            analytics = AnalyticsEngine(db)
            total_anomalies = 0
            
            for equipment in equipment_list:
                try:
                    # Run anomaly detection on primary metrics
                    # This is simplified - production would determine metrics per equipment type
                    metrics_to_check = get_metrics_for_equipment_type(equipment.equipment_type.value)
                    
                    for metric_name in metrics_to_check:
                        anomalies = analytics.detect_anomalies(
                            equipment_id=equipment.equipment_id,
                            metric_name=metric_name,
                            lookback_hours=24
                        )
                        
                        # Create alerts for detected anomalies
                        for anomaly in anomalies:
                            alert = Alert(
                                equipment_id=equipment.equipment_id,
                                alert_type="anomaly_detected",
                                severity=anomaly["severity"],
                                message=f"Anomaly detected in {metric_name}: "
                                       f"value {anomaly['metric_value']:.2f} at {anomaly['time']}",
                                metadata=anomaly
                            )
                            db.add(alert)
                            total_anomalies += 1
                    
                except Exception as e:
                    logger.error(f"Anomaly detection failed for {equipment.equipment_id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Anomaly detection complete. Found {total_anomalies} anomalies")
            
            return {
                "success": True,
                "equipment_checked": len(equipment_list),
                "anomalies_found": total_anomalies
            }
            
    except Exception as e:
        logger.error(f"Anomaly detection task failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="app.tasks.celery_app.generate_daily_reports")
def generate_daily_reports():
    """
    Generate automated daily compliance reports
    Runs at 1 AM daily
    """
    try:
        with get_db_context() as db:
            from app.models.database import ComplianceReport
            from app.api.reports.tasks import generate_report_task
            
            # Define yesterday's date range
            end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=1)
            
            # Create report record
            report = ComplianceReport(
                report_type="daily_summary",
                period_start=start_date,
                period_end=end_date,
                summary={"status": "generating"},
                created_by="automated_task"
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            logger.info(f"Generating daily report {report.report_id} for {start_date.date()}")
            
            # Generate report
            request_data = {
                "report_type": "daily_summary",
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "equipment_ids": None,
                "include_charts": True
            }
            
            generate_report_task(report.report_id, request_data)
            
            return {
                "success": True,
                "report_id": report.report_id,
                "period": f"{start_date.date()} to {end_date.date()}"
            }
            
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="app.tasks.celery_app.check_equipment_health_all")
def check_equipment_health_all():
    """
    Check health status of all equipment
    Generates alerts for equipment needing attention
    """
    try:
        with get_db_context() as db:
            analytics = AnalyticsEngine(db)
            
            equipment_list = db.query(Equipment).filter(
                Equipment.status == "active"
            ).all()
            
            logger.info(f"Checking health for {len(equipment_list)} equipment")
            
            alerts_created = 0
            
            for equipment in equipment_list:
                try:
                    # Get maintenance prediction
                    prediction = analytics.predict_maintenance(equipment.equipment_id)
                    
                    # Create alert if risk is high
                    if prediction.get("risk_level") == "high":
                        alert = Alert(
                            equipment_id=equipment.equipment_id,
                            alert_type="maintenance_required",
                            severity=AlertSeverity.WARNING,
                            message=f"Equipment requires maintenance: {prediction['recommendation']}",
                            metadata=prediction
                        )
                        db.add(alert)
                        alerts_created += 1
                    
                    # Check calibration due date
                    if equipment.next_calibration_due:
                        days_until_due = (equipment.next_calibration_due - datetime.utcnow()).days
                        
                        if days_until_due <= 7 and days_until_due > 0:
                            alert = Alert(
                                equipment_id=equipment.equipment_id,
                                alert_type="calibration_due_soon",
                                severity=AlertSeverity.INFO,
                                message=f"Calibration due in {days_until_due} days",
                                metadata={"due_date": equipment.next_calibration_due.isoformat()}
                            )
                            db.add(alert)
                            alerts_created += 1
                        elif days_until_due <= 0:
                            alert = Alert(
                                equipment_id=equipment.equipment_id,
                                alert_type="calibration_overdue",
                                severity=AlertSeverity.CRITICAL,
                                message=f"Calibration is {abs(days_until_due)} days overdue",
                                metadata={"due_date": equipment.next_calibration_due.isoformat()}
                            )
                            db.add(alert)
                            alerts_created += 1
                
                except Exception as e:
                    logger.error(f"Health check failed for {equipment.equipment_id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Health check complete. Created {alerts_created} alerts")
            
            return {
                "success": True,
                "equipment_checked": len(equipment_list),
                "alerts_created": alerts_created
            }
            
    except Exception as e:
        logger.error(f"Equipment health check task failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="app.tasks.celery_app.cleanup_old_data")
def cleanup_old_data():
    """
    Clean up old data beyond retention period
    Runs weekly
    """
    try:
        with get_db_context() as db:
            from sqlalchemy import text
            
            # Clean up old resolved alerts (keep for 1 year)
            alert_cutoff = datetime.utcnow() - timedelta(days=365)
            
            result = db.execute(
                text("""
                    DELETE FROM alerts 
                    WHERE resolved_at IS NOT NULL 
                      AND resolved_at < :cutoff
                """),
                {"cutoff": alert_cutoff}
            )
            
            alerts_deleted = result.rowcount
            
            # Clean up old reports
            report_cutoff = datetime.utcnow() - timedelta(days=settings.REPORT_RETENTION_DAYS)
            
            from app.models.database import ComplianceReport
            import os
            
            old_reports = db.query(ComplianceReport).filter(
                ComplianceReport.generated_at < report_cutoff
            ).all()
            
            for report in old_reports:
                # Delete file
                if report.file_path:
                    file_path = os.path.join(settings.REPORTS_OUTPUT_DIR, report.file_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                db.delete(report)
            
            reports_deleted = len(old_reports)
            
            db.commit()
            
            logger.info(f"Cleanup complete. Deleted {alerts_deleted} alerts, {reports_deleted} reports")
            
            return {
                "success": True,
                "alerts_deleted": alerts_deleted,
                "reports_deleted": reports_deleted
            }
            
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="app.tasks.celery_app.refresh_materialized_views")
def refresh_materialized_views():
    """
    Refresh materialized views for better query performance
    Runs every 30 minutes
    """
    try:
        with get_db_context() as db:
            from sqlalchemy import text
            
            # Refresh equipment health summary
            db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY equipment_health_summary"))
            
            db.commit()
            
            logger.info("Materialized views refreshed successfully")
            
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Materialized view refresh failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_metrics_for_equipment_type(equipment_type: str) -> list:
    """
    Helper function to determine which metrics to monitor per equipment type
    """
    metric_map = {
        "gas_detector": ["gas_concentration"],
        "temperature_sensor": ["temperature"],
        "pressure_sensor": ["pressure"],
        "air_quality_monitor": ["pm25", "pm10", "co2"],
        "location_tracker": ["battery_level"],
    }
    
    return metric_map.get(equipment_type, [])