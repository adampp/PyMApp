import inspect

from .registry import _registry

def send_message(recipient: str, message: object):
    stack = inspect.stack()
    worker_sender = True
    try:
        sender = stack[1][0].f_locals["self"]
    except KeyError:
        worker_sender = False
    else:
        if sender.name not in sender._sender_queues:
            worker_sender = False
    
    if not worker_sender:
        _registry.message_queues[recipient].put(message)
    else:
        sender._sender_queues[recipient].put(message)