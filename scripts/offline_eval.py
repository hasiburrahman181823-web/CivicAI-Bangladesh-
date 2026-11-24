"""Run a model evaluation with outbound network access blocked in this process."""
import os
import runpy
import sys

def deny_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
        raise PermissionError("Model evaluation runs with local files only.")

if __name__ == "__main__":
    os.environ.update({"HF_HUB_OFFLINE":"1", "HF_HUB_DISABLE_TELEMETRY":"1",
                       "TRANSFORMERS_OFFLINE":"1", "DO_NOT_TRACK":"1"})
    sys.addaudithook(deny_network)
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    module = sys.argv.pop(1)
    runpy.run_module(module, run_name="__main__", alter_sys=True)
