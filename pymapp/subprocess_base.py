import time
import uuid
import logging
import multiprocessing as mp
from collections.abc import Callable

from .stack_trace import full_stack
from .constants import *


class SubProcessBase():
    def __init__(
            self,
            main_target: Callable,
            main_loop_flag: bool = True,
            name: str = None,
            start_target: Callable = None,
            close_target: Callable = None,
            join_wait_time: int = 10,
            begin_flag: EventType = None,
            stop_flag: EventType = None,
        ) -> None:
        """
        Construct base subprocess class

        Parameters
        ----------
        main_target : Callable
            main worker function for this subprocess
        main_loop_flag : bool, optional
            whether or not to loop main_target, by default True
        name : str, optional
            name of this subprocess, by default None
        start_target : Callable, optional
            function to be called once prior to the main for this subprocess, by default None
        close_target : Callable, optional
            function to be called once after the end of the main worker for this subprocess, by default None
        logger : object, optional
            logger instance to write to, by default None
        join_wait_time : int, optional
            how long to wait (seconds) to gracefully close, by default 10
        begin_flag : multiprocessing.Event, optional
            enables synchronous starting of the main worker thread with other workers.
            the startup target runs  on start(), but the main will wait for this event to be set, by default None
        stop_flag : multiprocessing.Event, optional
            enables synchronous stopping of the main worker thread with other workers.
            the next time main_loop iterates, the subprocess will exit
        """
        if name is not None:
            self.name = name
        else:
            self.name = str(uuid.uuid4())

        self._main_target = main_target
        self._main_loop_flag = main_loop_flag
        self._start_target = start_target
        self._close_target = close_target
        self._join_wait_time = join_wait_time
        self._sync_begin_flag = begin_flag
        if stop_flag is None:
            self._sync_stop_flag = mp.Event()
        else:
            self._sync_stop_flag = stop_flag

        self.started_flag = mp.Event()
        self._hearbeat_flag = mp.Event()
        self._continue_flag = mp.Event()
        self._continue_flag.set()
        self._dead_flag = mp.Event()
        self._dont_kill_flag = mp.Event()

        self.subprocess_events = {
            EventDictKeys.SYNC_STOP: self._sync_stop_flag,
            EventDictKeys.DONT_KILL: self._dont_kill_flag,
            EventDictKeys.HEARTBEAT: self._hearbeat_flag,
            EventDictKeys.CONTINUE: self._continue_flag,
        }

        self._subprocess = mp.Process(
            target=self._main_loop,
            name=name,
        )

    def _try_call(self, try_func: Callable, *args, **kwargs) -> bool:
        """
        Tries to call function, logs error and stacktrace if failure

        Parameters
        ----------
        try_func : Callable
            function to try

        Returns
        -------
        bool
            True on success, False on failure
        """
        try:
            try_func(self.subprocess_events, *args, **kwargs)
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            stack_trace = full_stack()
            logging.error(f"{type(ex).__name__} : {str(ex)}:\n{stack_trace}")
            return False
        return True

    def _main_loop(self, *args, **kwargs) -> None:
        """
        Function in which main_target will be run (looped by default)
        """
        if self._start_target:
            self._try_call(self._start_target, *args, **kwargs)
            logging.info(f"Startup target for {self.name} complete")
        
        self.started_flag.set()


        while self._continue_flag.is_set() and not self._sync_stop_flag.is_set():
            if self._sync_begin_flag is not None and not self._sync_begin_flag.is_set():
                time.sleep(0.001)
                continue
            if self._try_call(self._main_target, *args, **kwargs):
                self._hearbeat_flag.set()
                if not self._main_loop_flag:
                    break
            else:
                break
        
        logging.info(f"Main loop for {self.name} complete")

        if self._close_target:
            self._try_call(self._close_target, *args, *kwargs)
            logging.info(f"Close target for {self.name} complete")
    

    def start(self) -> None:
        """
        Start the subprocess
        """
        logging.info(f"Starting process {self.name}")

        self._subprocess.start()

        logging.info(f"Started process {self.name}")

    
    def stop(self) -> None:
        """
        Stop the subprocess
        """
        logging.info(f"Stopping process {self.name}")
        
        self._continue_flag.clear()
        self._subprocess.join(self._join_wait_time)
        if self._subprocess.is_alive():
            self._subprocess.terminate()
            self._subprocess.join()
        
        logging.info(f"Stopped {self.name}")
    
    def get_heartbeat(self) -> bool:
        """
        Check heartbeat

        Returns
        -------
        bool
            True if heart has beat since last clear
        """
        return self._hearbeat_flag.is_set() or self._dont_kill_flag.is_set()
    
    def clear_heartbeat(self) -> None:
        """
        Clears heartbeat
        """
        self._hearbeat_flag.clear()
