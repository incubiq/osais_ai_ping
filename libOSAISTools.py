
## ------------------------------------------------------------------------
#       OSAIS python Tools (used by libOSAISVirtualAI.py)
## ------------------------------------------------------------------------

import uuid 
import subprocess as sp
import pkg_resources
import os
import platform
import ctypes
import threading

cuda=0                          ## from cuda import cuda, nvrtc
gVersionLibOSAIS="1.0.12"       ## version of this library (to keep it latest everywhere)
gObserver=None

## ------------------------------------------------------------------------
#       Observer (check updates in directory)
## ------------------------------------------------------------------------

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, fnOnFileCreated, _args):
        self.fnOnFileCreated = fnOnFileCreated
        self._args = _args

    def on_created(self, event):
        if event.is_directory:
            return
        if event.event_type == 'created':
            self.fnOnFileCreated(os.path.dirname(event.src_path), os.path.basename(event.src_path), self._args)

def start_observer_thread(path, fnOnFileCreated, _args):

    ## watch directory and call back if file was created
    def watch_directory(path, fnOnFileCreated, _args):    
        global gObserver
        if gObserver!=None:
            gObserver.stop()
        event_handler = NewFileHandler(fnOnFileCreated, _args)
        gObserver = Observer()
        gObserver.schedule(event_handler, path, recursive=False)
        gObserver.start()
        gObserver.join(1)

    thread = threading.Thread(target=watch_directory, args=(path, fnOnFileCreated, _args))
    thread.start()
    return watch_directory

def start_notification_thread(fnOnNotify):
    def _run(_fn):
        _fn()
    thread = threading.Thread(target=_run, args=(fnOnNotify))
    thread.start()
    return _run

## ------------------------------------------------------------------------
#       Directory utils
## ------------------------------------------------------------------------

## list content of a directory
def listDirContent(_dir):
    from os.path import isfile, join
    onlyfiles = [f for f in os.listdir(_dir)]
    ret="Found "+str (len(onlyfiles)) + " files in path "+_dir+"<br><br>";
    for x in onlyfiles:
        if isfile(join(_dir, x)):
            ret = ret+x+"<br>"
        else:
            ret = ret+"./"+x+"<br>"

    from datetime import datetime
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string+"<br>"+ret

def clearOldFiles(_dir):  
    from datetime import timedelta
    from datetime import datetime
    _now=datetime.now()
    cutoff_time = _now - timedelta(minutes=10)
    for filename in os.listdir(_dir):
        file_path = os.path.join(_dir, filename)
        modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if modification_time < cutoff_time:
            os.remove(file_path)
            
## ------------------------------------------------------------------------
#       System utils
## ------------------------------------------------------------------------

## get a meaningful name for our machine
def get_machine_name() :
    _machine=str (hex(uuid.getnode()))
    _isDocker=is_running_in_docker()
    if _isDocker:
        _machine = os.environ.get('HOSTNAME') or os.popen('hostname').read().strip()
    return _machine

## which OS are we running on?
def get_os_name():
    os_name = platform.system()
    return os_name

## Are we running inside a docker session?
def is_running_in_docker():
    if os.path.exists('/proc/self/cgroup'):
        with open('/proc/self/cgroup', 'rt') as f:
            return 'docker' in f.read()
    return False

## get ip address of the host
def get_container_ip():
    import socket

    # Get the hostname of the machine running the script
    hostname = socket.gethostname()

    # Get the IP address of the container by resolving the hostname
    ip_address = socket.gethostbyname(hostname)
    return ip_address

## get our external ip address
def get_external_ip():
    import requests
    url = "https://api.ipify.org"
    response = requests.get(url)
    return response.text.strip()

## get our external port
def get_port(): 
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    return port

## just to get the list of all installed Python modules in the running session
def get_list_of_modules():
    installed_packages = pkg_resources.working_set
    installed_packages_list=[]
    for i in installed_packages:
        installed_packages_list.append({i.key: i.version})
    return installed_packages_list

## ------------------------------------------------------------------------
#       GPU utils
## ------------------------------------------------------------------------

## which GPU is this? (will require access to nvidia-smi)
def get_gpu_attr(_attr):
   output_to_list = lambda x: x.decode('ascii').split('\n')[:-1]
   COMMAND = "nvidia-smi --query-gpu="+_attr+" --format=csv"
   try:
        memory_use_info = output_to_list(sp.check_output(COMMAND.split(),stderr=sp.STDOUT))[1:]
   except sp.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
   memory_use_values = [x.replace('\r', '') for i, x in enumerate(memory_use_info)]
   return memory_use_values


## get GPU Cuda info
# see here: https://gist.github.com/tispratik/42a71cae34389fd7c8e89496ae8813ae
def getCudaInfo():
    
    display_name = "no GPU"
    display_cores = "0"
    display_major = "0"
    display_minor = "0"

    if cuda:
        CUDA_SUCCESS = 0
        CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT = 16
        CU_DEVICE_ATTRIBUTE_MAX_THREADS_PER_MULTIPROCESSOR = 39
        CU_DEVICE_ATTRIBUTE_CLOCK_RATE = 13
        CU_DEVICE_ATTRIBUTE_MEMORY_CLOCK_RATE = 36

        nGpus = ctypes.c_int()
        name = b' ' * 100
        cc_major = ctypes.c_int()
        cc_minor = ctypes.c_int()
        cores = ctypes.c_int()
        threads_per_core = ctypes.c_int()
        clockrate = ctypes.c_int()
        freeMem = ctypes.c_size_t()
        totalMem = ctypes.c_size_t()

        result = ctypes.c_int()
        device = ctypes.c_int()
        context = ctypes.c_void_p()
        error_str = ctypes.c_char_p()

        result=cuda.cuInit(0)
        if(result != CUDA_SUCCESS):
            print("error %d " % (result))
            return 0
        
        if(cuda.cuDeviceGetCount(ctypes.byref(nGpus)) != CUDA_SUCCESS):
            return 0

        for i in range(nGpus.value):

            # get device
            if(cuda.cuDeviceGet(ctypes.byref(device), i) != CUDA_SUCCESS):
                return 0
            if (cuda.cuDeviceComputeCapability(ctypes.byref(cc_major), ctypes.byref(cc_minor), device) != CUDA_SUCCESS):  
                return 0
            if (cuda.cuDeviceGetName(ctypes.c_char_p(name), len(name), device) != CUDA_SUCCESS): 
                return 0
            if(cuda.cuDeviceGetAttribute(ctypes.byref(cores), CU_DEVICE_ATTRIBUTE_MULTIPROCESSOR_COUNT, device) != CUDA_SUCCESS):
                return 0

        display_name=name.split(b'\0', 1)[0].decode()
        display_major=cc_major.value
        display_minor=cc_minor.value
        display_cores=cores.value * _ConvertSMVer2Cores(cc_major.value, cc_minor.value)

    return {
        "name": display_name,
        "compute_major": display_major,
        "compute_minor": display_minor,
        "cuda cores": display_cores 
    }

def _ConvertSMVer2Cores(major, minor):
    # Returns the number of CUDA cores per multiprocessor for a given
    # Compute Capability version. There is no way to retrieve that via
    # the API, so it needs to be hard-coded.
    return {
    # Tesla
      (1, 0):   8,      # SM 1.0
      (1, 1):   8,      # SM 1.1
      (1, 2):   8,      # SM 1.2
      (1, 3):   8,      # SM 1.3
    # Fermi
      (2, 0):  32,      # SM 2.0: GF100 class
      (2, 1):  48,      # SM 2.1: GF10x class
    # Kepler
      (3, 0): 192,      # SM 3.0: GK10x class
      (3, 2): 192,      # SM 3.2: GK10x class
      (3, 5): 192,      # SM 3.5: GK11x class
      (3, 7): 192,      # SM 3.7: GK21x class
    # Maxwell
      (5, 0): 128,      # SM 5.0: GM10x class
      (5, 2): 128,      # SM 5.2: GM20x class
      (5, 3): 128,      # SM 5.3: GM20x class
    # Pascal
      (6, 0):  64,      # SM 6.0: GP100 class
      (6, 1): 128,      # SM 6.1: GP10x class
      (6, 2): 128,      # SM 6.2: GP10x class
    # Volta
      (7, 0):  64,      # SM 7.0: GV100 class
      (7, 2):  64,      # SM 7.2: GV11b class
    # Turing
      (7, 5):  64,      # SM 7.5: TU10x class
    }.get((major, minor), 64)   # unknown architecture, return a default value

## ------------------------------------------------------------------------
#       getInfo endoint
## ------------------------------------------------------------------------

## get various info about this host
def getHostInfo(_engine):
    from datetime import datetime
    now = datetime.now()
    objGPU={}
    objGPU["memory_free"]=get_gpu_attr("memory.free")[0]
    objGPU["memory_used"]=get_gpu_attr("memory.used")[0]
    objGPU["name"]=get_gpu_attr("gpu_name")[0]
    objGPU["driver_version"]=get_gpu_attr("driver_version")[0]
    objGPU["temperature"]=get_gpu_attr("temperature.gpu")[0]
    objGPU["utilization"]=get_gpu_attr("utilization.gpu")[0]

    objCuda=getCudaInfo()        
    return {
        "datetime": now.strftime("%d/%m/%Y %H:%M:%S"), 
        "isDocker": is_running_in_docker(),
        "internal IP": get_container_ip(),
        "port": get_port(),
        "engine": _engine,
        "machine": get_machine_name(),
        "GPU": objGPU,
        "Cuda": objCuda,
        "modules": get_list_of_modules()
    }

## ------------------------------------------------------------------------
#       File / Image utils
## ------------------------------------------------------------------------

## downloads an image as file from external URL
def downloadImage(url) :
    import urllib.request

    # Determine the file name and extension of the image based on the URL.
    file_name, file_extension = os.path.splitext(url)
    
    # Define the local file path where the image will be saved.
    spliter='/'
    local_filename=file_name.split(spliter)[-1]
    local_file_path = f"./_input/{local_filename}{file_extension}"
    
    # Download the image from the URL and save it locally.
    urllib.request.urlretrieve(url, local_file_path)
    return f"{local_filename}{file_extension}"

