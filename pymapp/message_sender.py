from .registry import _registry

def send_message(recipient: str, message: object):
    _registry.mapp_class._message_queues[recipient].put(message)