"""
Utility functions for FlightPortal.
Includes memory management, debug logging, and error handling.
"""

import sys

# Check if running on CircuitPython or standard Python
is_circuitpython = sys.implementation.name == 'circuitpython'

if is_circuitpython:
    import gc
else:
    import gc as std_gc

# Debug flag - set to True for verbose logging
DEBUG_MODE = False

def set_debug(enabled):
    """Enable or disable debug mode."""
    global DEBUG_MODE
    DEBUG_MODE = enabled
    if enabled:
        debug_print("DEBUG MODE ENABLED")

def debug_print(message):
    """Print a debug message if debug mode is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def log_error(message, error=None):
    """Log an error message with optional exception details."""
    print(f"[ERROR] {message}")
    if error:
        print(f"[ERROR] Exception: {error.__class__.__name__}: {error}")

def log_info(message):
    """Log an info message."""
    print(f"[INFO] {message}")

def log_warning(message):
    """Log a warning message."""
    print(f"[WARN] {message}")

def get_free_memory():
    """Return the amount of free memory in bytes."""
    if is_circuitpython:
        return gc.mem_free()
    else:
        # Standard Python doesn't have mem_free
        try:
            import psutil
            return psutil.virtual_memory().available
        except ImportError:
            return 8192  # 8KB placeholder for testing

def get_allocated_memory():
    """Return the amount of allocated memory in bytes."""
    if is_circuitpython:
        return gc.mem_alloc()
    else:
        # Standard Python doesn't have mem_alloc
        try:
            import psutil
            return psutil.virtual_memory().used
        except ImportError:
            return 4096  # 4KB placeholder for testing

def print_memory_status():
    """Print current memory usage statistics."""
    if is_circuitpython:
        free = get_free_memory()
        alloc = get_allocated_memory()
        total = free + alloc
        pct_used = (alloc / total * 100) if total > 0 else 0
        print(f"[MEM] Free: {free} bytes | Allocated: {alloc} bytes | Total: {total} bytes | Usage: {pct_used:.1f}%")
    else:
        debug_print("Memory status (not available on standard Python)")

def collect_garbage():
    """Run garbage collection and return freed memory."""
    if is_circuitpython:
        before = get_free_memory()
        gc.collect()
        after = get_free_memory()
        freed = after - before
        debug_print(f"Garbage collection freed {freed} bytes")
        return freed
    else:
        std_gc.collect()
        debug_print("Garbage collection completed")
        return 0

class MemoryBuffer:
    """Pre-allocated fixed-size byte buffer for memory-constrained environments."""
    
    def __init__(self, size):
        """Create a buffer of specified size."""
        self.size = size
        self.buffer = bytearray(size)
        self.length = 0
    
    def clear(self):
        """Clear all data in the buffer."""
        for i in range(self.size):
            self.buffer[i] = 0
        self.length = 0
    
    def write(self, data, offset=0):
        """Write data to buffer at specified offset."""
        data_len = len(data)
        if offset + data_len > self.size:
            raise MemoryError(f"Out of buffer space: {offset + data_len} > {self.size}")
        
        for i in range(data_len):
            self.buffer[offset + i] = data[i]
        self.length = max(self.length, offset + data_len)
        return data_len
    
    def get_bytes(self):
        """Get the buffer contents as bytes."""
        return bytes(self.buffer[:self.length])
    
    def find(self, pattern):
        """Find a pattern in the buffer, return index or -1."""
        pattern_len = len(pattern)
        for i in range(self.length - pattern_len + 1):
            match = True
            for j in range(pattern_len):
                if self.buffer[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                return i
        return -1
    
    def truncate_at(self, index):
        """Truncate buffer at specified index."""
        if index < 0 or index > self.size:
            raise ValueError(f"Invalid truncate index: {index}")
        self.length = index
