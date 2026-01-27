"""
Worker Pool for Parallel Conversion
Manages parallel conversion of multiple files simultaneously
"""

import time
import threading
from queue import Queue, Empty
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class WorkerStatus(Enum):
    """Worker status enumeration"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkItem:
    """Work item for conversion queue"""
    file_info: Dict[str, Any]
    context: Dict[str, Any]
    level: int
    use_fast_model: bool = True


@dataclass
class WorkResult:
    """Result from conversion worker"""
    file_path: str
    go_code: Optional[str]
    success: bool
    error: Optional[str]
    elapsed_time: float
    cached: bool
    model_used: str


class ConversionWorker(threading.Thread):
    """Worker thread for converting files"""
    
    def __init__(
        self,
        worker_id: int,
        work_queue: Queue,
        result_queue: Queue,
        converter,
        logger,
        stop_event: threading.Event
    ):
        """
        Initialize conversion worker
        
        Args:
            worker_id: Unique worker identifier
            work_queue: Queue to get work items from
            result_queue: Queue to put results in
            converter: AIConverter instance
            logger: Logger instance
            stop_event: Event to signal worker to stop
        """
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.converter = converter
        self.logger = logger
        self.stop_event = stop_event
        self.status = WorkerStatus.IDLE
        self.current_file = None
    
    def run(self):
        """Worker main loop"""
        while not self.stop_event.is_set():
            try:
                # Get work item with timeout
                work_item = self.work_queue.get(timeout=0.5)
                
                # Update status
                self.status = WorkerStatus.WORKING
                self.current_file = work_item.file_info['name']
                
                # Process work item
                result = self._process_work_item(work_item)
                
                # Put result in queue
                self.result_queue.put(result)
                
                # Mark task as done
                self.work_queue.task_done()
                
                # Update status
                self.status = WorkerStatus.IDLE
                self.current_file = None
                
            except Empty:
                # No work available, continue waiting
                continue
            except Exception as e:
                self.logger.error(f"Worker {self.worker_id} error: {e}")
                self.status = WorkerStatus.FAILED
    
    def _process_work_item(self, work_item: WorkItem) -> WorkResult:
        """
        Process a single work item
        
        Args:
            work_item: Work item to process
            
        Returns:
            WorkResult with conversion result
        """
        file_info = work_item.file_info
        file_path = file_info['path']
        start_time = time.time()
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check cache
            cached = False
            if self.converter.redis_store.is_available():
                file_changed = self.converter.redis_store.file_changed(file_path, content)
                
                if not file_changed:
                    cached_result = self.converter.redis_store.get_conversion_output(file_path)
                    if cached_result:
                        elapsed_time = time.time() - start_time
                        return WorkResult(
                            file_path=file_path,
                            go_code=cached_result['go_code'],
                            success=True,
                            error=None,
                            elapsed_time=elapsed_time,
                            cached=True,
                            model_used='cache'
                        )
            
            # Convert file
            model_used = 'fast' if work_item.use_fast_model else 'smart'
            go_code = self.converter._convert_file_with_model(
                file_info,
                work_item.context,
                use_fast_model=work_item.use_fast_model
            )
            
            elapsed_time = time.time() - start_time
            
            # Cache result
            if self.converter.redis_store.is_available() and go_code:
                go_module = self.converter._determine_go_module(file_info['name'])
                self.converter.redis_store.store_conversion_output(
                    file_path,
                    go_code,
                    {'module': go_module, 'model': model_used}
                )
            
            return WorkResult(
                file_path=file_path,
                go_code=go_code,
                success=True,
                error=None,
                elapsed_time=elapsed_time,
                cached=False,
                model_used=model_used
            )
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            return WorkResult(
                file_path=file_path,
                go_code=None,
                success=False,
                error=str(e),
                elapsed_time=elapsed_time,
                cached=False,
                model_used='error'
            )


class WorkerPool:
    """Manages a pool of conversion workers"""
    
    def __init__(
        self,
        converter,
        logger,
        num_workers: int = 4
    ):
        """
        Initialize worker pool
        
        Args:
            converter: AIConverter instance
            logger: Logger instance
            num_workers: Number of worker threads
        """
        self.converter = converter
        self.logger = logger
        self.num_workers = num_workers
        
        self.work_queue = Queue()
        self.result_queue = Queue()
        self.stop_event = threading.Event()
        
        self.workers = []
        self.results = []
        
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads"""
        self.logger.info(f"🚀 Starting {self.num_workers} conversion workers...")
        
        for i in range(self.num_workers):
            worker = ConversionWorker(
                worker_id=i,
                work_queue=self.work_queue,
                result_queue=self.result_queue,
                converter=self.converter,
                logger=self.logger,
                stop_event=self.stop_event
            )
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"✓ {self.num_workers} workers ready")
    
    def submit_work(self, work_items: List[WorkItem]):
        """
        Submit work items to the pool
        
        Args:
            work_items: List of work items to process
        """
        for item in work_items:
            self.work_queue.put(item)
    
    def wait_for_completion(self, total_items: int) -> List[WorkResult]:
        """
        Wait for all work to complete and collect results
        
        Args:
            total_items: Total number of items submitted
            
        Returns:
            List of WorkResult objects
        """
        results = []
        completed = 0
        
        while completed < total_items:
            try:
                result = self.result_queue.get(timeout=1.0)
                results.append(result)
                completed += 1
                
                # Log progress
                file_name = Path(result.file_path).name
                status = "✓" if result.success else "✗"
                cache_flag = " [CACHED]" if result.cached else ""
                model_flag = f" [{result.model_used}]" if not result.cached else ""
                
                self.logger.info(
                    f"{status} ({completed}/{total_items}) {file_name} "
                    f"({result.elapsed_time:.2f}s){cache_flag}{model_flag}"
                )
                
            except Empty:
                # Check if workers are still alive
                alive_workers = sum(1 for w in self.workers if w.is_alive())
                if alive_workers == 0:
                    self.logger.warning("All workers terminated unexpectedly")
                    break
        
        return results
    
    def shutdown(self):
        """Shutdown worker pool"""
        self.logger.info("🛑 Shutting down worker pool...")
        
        # Signal workers to stop
        self.stop_event.set()
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=2.0)
        
        self.logger.info("✓ Worker pool shut down")
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get current status of all workers"""
        return {
            'total_workers': self.num_workers,
            'working': sum(1 for w in self.workers if w.status == WorkerStatus.WORKING),
            'idle': sum(1 for w in self.workers if w.status == WorkerStatus.IDLE),
            'queue_size': self.work_queue.qsize(),
            'workers': [
                {
                    'id': w.worker_id,
                    'status': w.status.value,
                    'current_file': w.current_file
                }
                for w in self.workers
            ]
        }


from pathlib import Path
