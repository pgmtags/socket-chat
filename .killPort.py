import psutil
import sys


def find_process_using_port(port):
    connections = psutil.net_connections(kind='inet')
    for conn in connections:
        if conn.laddr.port == port:
            try: return psutil.Process(conn.pid)
            except psutil.NoSuchProcess: continue
    return None


def kill_process_using_port(port):
    process = find_process_using_port(port)
    if process:
        process.kill()
        print(f"Process {process.pid} ({process.name()}) has been killed.")
    else: print(f"No process using the port {port}.")


try: kill_process_using_port(int(sys.argv[1]))
except IndexError: print("The entered port is not registered.")
