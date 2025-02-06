import json
from metrics.local_metrics import LocalMetrics

def get_system_metrics(logger):
    """Main function to collect local metrics"""
    try:
        local = LocalMetrics(logger)
        metrics = local.get_metrics()
        
        # Log metrics
        logger.info(json.dumps(metrics))
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error in get_system_metrics: {str(e)}")
        return None