import logging
import sys
import os

def setup_logger(name="api", level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # Also write to local logs if directory exists
        try:
            log_dir = "../storage/logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            fh = logging.FileHandler(os.path.join(log_dir, "api.log"))
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass
            
    return logger
