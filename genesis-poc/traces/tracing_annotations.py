from aws_xray_sdk.core import xray_recorder
from functools import wraps

def xray_trace(name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            segment = xray_recorder.begin_segment(name)
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                segment.put_metadata(
                    'error',
                    {
                        'message': f'{name} failed',
                        'details': str(e)
                    }
                )
                raise
            finally:
                xray_recorder.end_segment()
        return wrapper
    return decorator