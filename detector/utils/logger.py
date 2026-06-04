import logging
import sys

def setup_logger(name="detector", level=logging.INFO):
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
            os_log_path = "../storage/logs/detector.log"
            if os.path.exists("../storage/logs"):
                fh = logging.FileHandler(os_log_path)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
        except Exception:
            pass
            
    return logger
