import logging
import re
import os
import configparser
import shutil
import uuid
import time
import sys
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_session import Session
from cachelib.file import FileSystemCache
from multiprocessing import Process, Queue
from waitress import serve
from pathlib import Path
import multiprocessing as mp
from ._version import __version__

class Webservice:
    
    def __init__(self, config):
        #solve reload problem when using spawn method (osx/windows)
        if mp.get_start_method()=="spawn":
            frame = sys._getframe()
            while frame:
                if "__name__" in frame.f_locals.keys():
                    if not frame.f_locals["__name__"]=="__main__":
                        return
                frame = frame.f_back
        #set variables
        self.location = os.path.dirname(os.path.abspath(__file__))
        self.logger = logging.getLogger("webservice")
        self.config = configparser.ConfigParser()
        self.config.read(config)
        #logger modus
        if self.config.getboolean("webservice","debug",fallback=False):
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("run in debug mode")
        else:
            self.logger.setLevel(logging.INFO)
        #define services
        services = self.config.get("webservice","services",fallback=None)
        self.services = []
        if not services is None:
            for service in services.split(","):
                service = service.strip()
                if service in self.config:
                    if not "name" in self.config[service]:
                        self.logger.error("service '%s' has no 'name' configured" % service)
                    elif not "config" in self.config[service]:
                        self.logger.error("service '%s' has no 'config' configured" % service)
                    else:
                        self.services.append(service)
                else:
                    self.logger.error("service '%s' not configured" % service)
        #clear temporary directory
        self.tmp = os.path.abspath(self.config.get("webservice","tmp",fallback="tmp"))
        for root, dirs, files in os.walk(self.tmp):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        #create structure
        os.mkdir(os.path.join(self.tmp, "data"))
        for service in self.services:
            os.mkdir(os.path.join(self.tmp, "data", service))


    def validationWorker(queue):
        print(os.getpid(),"working")
        while True:
            item = queue.get(block=True)
            if item is None:
                break
            print(os.getpid(), "got", item)
            time.sleep(1) # simulate a "long" operation
        
    def service(self):
        nWorkers = 3
        try:
            self.logger.debug("start queue for validation")
            validationQueue = mp.Queue()
            self.logger.debug("start pool with %d validation workers" % nWorkers)
            pool = mp.Pool(3, Webservice.validationWorker,(validationQueue,))
            for i in range(2):
                validationQueue.put(("hello",123))
            self.webservice()
        finally:
            for i in range(nWorkers):
                validationQueue.put(None)
            validationQueue.close()
            validationQueue.join_thread()
            pool.close()
            pool.join()



    def webservice(self):
        #--- initialize Flask application ---  
        logging.getLogger("werkzeug").disabled = True
        app = Flask(__name__, static_url_path="/static", 
                    static_folder=os.path.join(self.location,"static"), 
                    template_folder=os.path.join(self.location,"templates"))
        #further settings
        app.debug = self.config.getboolean("webservice","debug",fallback=False)
        #temporary, remove if finished
        app.debug = True
        app.config["config"] = self.config
        app.config["location"] = self.location
        
        
        #session
        app.config["SESSION_PERMANENT"] = False
        app.config["SESSION_TYPE"] = "cachelib"
        app.config["SESSION_COOKIE_NAME"] = "excel-validator"
        app.config["SESSION_CACHELIB"] = FileSystemCache(cache_dir=os.path.join(self.tmp, "session"), threshold=500)
        Session(app)
        
        @app.route("/", methods=["GET", "POST"])
        @app.route("/<path:path>", methods=["GET", "POST"])
        def index(path=""):
            #uid
            session["uid"] = session.get("uid", uuid.uuid4().hex)
            # parse url
            pattern = re.compile(r"[^\/]+\/")
            rootLocation = "../"*len(re.findall(pattern, path))
            pathSplits = path.split("/")
            operation = pathSplits[0]
            subOperation = pathSplits[1] if len(pathSplits)>1 else None
            variables = {
                "path": path,
                "operation": operation,
                "title": self.config.get("webservice","title",fallback="Excel Validator"),
                "textFooter": self.config.get("webservice","text.footer",
                    fallback="""
                        This tool is powered by 
                        <a target=\"_blank\" href=\"https://pypi.org/project/excel-validator/\">excel-validator</a> version %s - 
                        developed as part of the <a target=\"_blank\" href=\"https://agent-project.eu/\">H2020 AGENT</a> project
                    """ % __version__)
            }
            if operation=="":
                variables["services"] = [[service,self.config.get(service,"name",fallback=service)] 
                                         for service in self.services]
                variables["textIntro"] = self.config.get("webservice","text.intro",fallback="Select the required validation")
                return render_template("index.html", **variables)
            elif operation in self.services:
                #set variables
                variables["api"] = "%s/api" % operation
                if subOperation == "api":
                    uploadDirectory = os.path.join(self.tmp,"data",operation,"%s" % session["uid"])
                    if request.method == "POST":
                        if "file" in request.files:
                            #only if no upload present
                            if not (os.path.exists(uploadDirectory) or session.get("%s.upload" % operation, False)):
                                uploaded_file = request.files["file"]
                                if uploaded_file.filename != "":
                                    os.mkdir(uploadDirectory)
                                    uploaded_file.save(os.path.join(uploadDirectory,"original.xlsx"))
                                    session["%s.upload" % operation] = os.path.basename(uploaded_file.filename)
                                    print("stored %s for %s" % (os.path.basename(uploaded_file.filename), session["uid"]))
                        elif "action" in request.form:
                            if request.form["action"]=="delete":
                                shutil.rmtree(uploadDirectory)
                                session.pop("%s.upload" % operation)
                    #compute status
                    status = {
                        "upload": False
                    }
                    if os.path.exists(uploadDirectory):
                        uploadFilename = os.path.join(uploadDirectory,"original.xlsx")
                        if not session.get("%s.upload" % operation, False):
                            shutil.rmtree(uploadDirectory)
                        elif not os.path.exists(uploadFilename):
                            shutil.rmtree(uploadDirectory)
                        else:
                            status["upload"] = True
                            status["filename"] = session.get("%s.upload" % operation, False)
                            fileStats = os.stat(uploadFilename)
                            status["filesize"] = fileStats.st_size
                            status["filetime"] = int(fileStats.st_ctime)
                    elif session.get("%s.upload" % operation, False):
                        session.pop("%s.upload" % operation)
                    return jsonify(status)
                else:
                    variables["name"] = self.config.get(operation,"name",fallback=operation)
                    variables["textUpload"] = self.config.get(operation,"text.upload",fallback="Select XLSX File for validation")
                    return render_template("service.html", **variables)
            else:
                return redirect(url_for("index"))

        #start webservice
        self.logger.debug("start webservice")
        serve(app, 
                  host=self.config["webservice"].get("host", "::"), 
                  port=self.config["webservice"].get("port", "8080"), 
                  threads=self.config["webservice"].get("threads", "10")) 
        



