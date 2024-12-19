import logging
import re
import os
import configparser
import shutil
import uuid
import time
import sys
import json
import zipfile
import datetime
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, session, request, jsonify, current_app, make_response
from flask_session import Session
from cachelib.file import FileSystemCache
from multiprocessing import Process, Queue
from waitress import serve
from pathlib import Path
import func_timeout
import multiprocessing as mp
from ._version import __version__
from . import validator

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
        os.makedirs(self.tmp, exist_ok=True)
        for root, dirs, files in os.walk(self.tmp):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        #create structure
        os.mkdir(os.path.join(self.tmp, "data"))
        for service in self.services:
            os.mkdir(os.path.join(self.tmp, "data", service))


    def validationWorker(dataLocation,config,queue,status,debug):
        #logger
        logger = logging.getLogger("validation_%s" % os.getpid())
        timeoutPeriod = config.getint("validation","timeout",fallback=500)
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("run in debug mode, timeout after %s seconds" % timeoutPeriod)
        else:
            logger.setLevel(logging.INFO)
        #loop
        while True:
            item = queue.get(block=True)
            if item is None:
                break
            #get variables
            service = item[0]
            sessionIdentifier = item[1]
            uploadIdentifier = item[2]
            uploadFilename = item[3]
            validationIdentifier = item[4]
            formData = item[5]
            try:  
                if not status.get(validationIdentifier, None) is None:
                    logger.debug("started validation %s from %s" % (service, uploadFilename))
                    #validate
                    configFilename = validator.Validate.getConfigFilename(config.get(service,"config"))
                    uploadDirectory = os.path.join(dataLocation,service,"%s" % sessionIdentifier)
                    xlsxFilename = os.path.join(uploadDirectory,"%s" % uploadIdentifier)
                    updateFilename = os.path.join(uploadDirectory,"%s" % uploadFilename)
                    shutil.copyfile(xlsxFilename,updateFilename)
                    #do validation
                    try:
                        validation = func_timeout.func_timeout(timeoutPeriod, validator.Validate, (updateFilename, configFilename, ), 
                                              {"updateFile": True, "statusRegister": status, 
                                               "statusIdentifier": validationIdentifier, "webinterfaceData": formData})
                        #create package and reports
                        packageFilename = os.path.join(uploadDirectory,"%s.json" % validationIdentifier)
                        validation.createPackageJSON(packageFilename)                        
                        reportFilename = os.path.join(uploadDirectory,"%s.report.json" % validationIdentifier)
                        validation.createReport(reportFilename)
                        reportTextFilename = os.path.join(uploadDirectory,"%s.report.txt" % validationIdentifier)
                        validation.createTextReport(reportTextFilename)
                        reportMarkdownFilename = os.path.join(uploadDirectory,"%s.report.md" % validationIdentifier)
                        validation.createMarkdownReport(reportMarkdownFilename)
                        logger.debug("ended validation %s from %s" % (service, uploadFilename))
                    except func_timeout.FunctionTimedOut:
                        logger.debug("timeout validation %s from %s after %s seconds" % (service, uploadFilename, timeoutPeriod))
                        if validationIdentifier in status:
                            statusEntry = status[validationIdentifier]
                            statusEntry.update({"error": "timeout validation %s after %s seconds" % 
                                                (uploadFilename, timeoutPeriod, )})
                            status.update({validationIdentifier: statusEntry})
                else:
                    logger.debug("aborted validation %s from %s" % (service, uploadFilename))
            except Exception as e:
                logger.debug("failed validation %s from %s: %s" % (service, uploadFilename, e))
                if validationIdentifier in status:
                    statusEntry = status[validationIdentifier]
                    statusEntry.update({"error": "validation failed: %s" % str(e)})
                    status.update({validationIdentifier: statusEntry})
                    
        
    def service(self):
        nWorkers = self.config.getint("validation","threads",fallback=3)
        try:
            self.logger.debug("start queue for validation")
            manager = mp.Manager()
            validationStatus = manager.dict()
            validationQueue = mp.Queue()
            self.logger.debug("start pool with %d validation workers" % nWorkers)
            pool = mp.Pool(nWorkers, Webservice.validationWorker,(os.path.join(self.tmp,"data"),
                                                                  self.config,validationQueue,validationStatus,
                                                                  self.config.getboolean("webservice","debug",fallback=False)))
            self.webservice(validationQueue,validationStatus)
        finally:
            for i in range(nWorkers):
                validationQueue.put(None)
            validationQueue.close()
            validationQueue.join_thread()
            pool.close()
            pool.join()

    def webservice(self,validationQueue, validationStatus):
        #--- initialize Flask application ---  
        logging.getLogger("werkzeug").disabled = True
        app = Flask(__name__, static_url_path="/static", 
                    static_folder=os.path.join(self.location,"static"), 
                    template_folder=os.path.join(self.location,"templates"))
        #further settings
        app.debug = self.config.getboolean("webservice","debug",fallback=False)
        #temporary, remove if finished
        app.debug = True
        app.config["logger"] = self.logger
        app.config["config"] = self.config
        app.config["location"] = self.location
        app.config["queue"] = validationQueue
        app.config["status"] = validationStatus
        
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
                            if session.get("%s.upload" % operation, None) is None:
                                #remove if upload directory exists (should not happen)
                                if os.path.exists(uploadDirectory):
                                    shutil.rmtree(uploadDirectory)
                                #reset session (should not be necessary)
                                session["%s.identifier" % operation] = ""
                                session.pop("%s.identifier" % operation)
                                session["%s.validate" % operation] = ""
                                session.pop("%s.validate" % operation)
                                #store new file
                                uploaded_file = request.files["file"]
                                if uploaded_file.filename != "":
                                    os.mkdir(uploadDirectory)
                                    uploadIdentifier = uuid.uuid4().hex
                                    uploaded_file.save(os.path.join(uploadDirectory,"%s" % uploadIdentifier))
                                    session["%s.identifier" % operation] = uploadIdentifier
                                    session["%s.upload" % operation] = os.path.basename(uploaded_file.filename)
                                    current_app.config["logger"].debug("%s: stored %s for %s as %s" % 
                                        (operation, os.path.basename(uploaded_file.filename), 
                                         session["uid"], uploadIdentifier))
                                else:
                                    current_app.config["logger"].error("%s: could not store file for %s " % (operation, session["uid"]))
                            else:
                                current_app.config["logger"].error("%s: could not store file for %s because of existing upload" % 
                                                                   (operation, session["uid"]))
                        elif "action" in request.form:
                            if session.get("%s.upload" % operation, None) is None:
                                current_app.config["logger"].error("%s: no upload present for %s" % (operation, session["uid"]))
                            elif request.form["action"]=="delete":
                                shutil.rmtree(uploadDirectory)
                                validationIdentifier = session.get("%s.validate" % operation, None)
                                uploadIdentifier = session.get("%s.identifier" % operation, None)
                                uploadFilename = session.get("%s.upload" % operation, None)
                                session["%s.identifier" % operation] = ""
                                session.pop("%s.identifier" % operation)
                                session["%s.upload" % operation] = ""
                                session.pop("%s.upload" % operation)
                                if not validationIdentifier is None:
                                    if validationIdentifier in current_app.config["status"]:
                                        current_app.config["status"].pop(validationIdentifier)
                                    current_app.config["logger"].debug("%s: aborted validation %s for %s" % 
                                                                       (operation, validationIdentifier, session["uid"]))
                                if not uploadIdentifier is None:
                                    current_app.config["logger"].debug("%s: deleted upload %s for %s" % 
                                                                       (operation, uploadFilename, session["uid"]))
                            elif (request.form["action"]=="abort") or (request.form["action"]=="reset"):
                                validationIdentifier = session.get("%s.validate" % operation, None)
                                uploadIdentifier = session.get("%s.identifier" % operation, None)
                                uploadFilename = session.get("%s.upload" % operation, None)
                                session["%s.validate" % operation] = ""
                                session.pop("%s.validate" % operation)
                                if not validationIdentifier is None:
                                    updateFilename = os.path.join(uploadDirectory,"%s" % uploadFilename)
                                    packageFilename = os.path.join(uploadDirectory,"%s.json" % validationIdentifier)
                                    reportFilename = os.path.join(uploadDirectory,"%s.report.json" % validationIdentifier)
                                    reportTextFilename = os.path.join(uploadDirectory,"%s.report.txt" % validationIdentifier)
                                    reportMarkdownFilename = os.path.join(uploadDirectory,"%s.report.md" % validationIdentifier)
                                    if os.path.exists(updateFilename):
                                        os.remove(updateFilename)
                                    if os.path.exists(packageFilename):
                                        os.remove(packageFilename)
                                    if os.path.exists(reportFilename):
                                        os.remove(reportFilename)
                                    if os.path.exists(reportTextFilename):
                                        os.remove(reportTextFilename)
                                    if os.path.exists(reportMarkdownFilename):
                                        os.remove(reportMarkdownFilename)
                                    if validationIdentifier in current_app.config["status"]:
                                        current_app.config["status"].pop(validationIdentifier)
                                    if request.form["action"]=="abort":
                                        current_app.config["logger"].debug("%s: aborted validation %s from %s for %s" % 
                                                            (operation, validationIdentifier, uploadFilename, session["uid"]))
                                    elif request.form["action"]=="reset":
                                        current_app.config["logger"].debug("%s: reset validation %s from %s for %s" % 
                                                            (operation, validationIdentifier, uploadFilename, session["uid"]))
                            elif request.form["action"]=="validate":
                                validationIdentifier = session.get("%s.validate" % operation, None)
                                uploadIdentifier = session.get("%s.identifier" % operation, None)
                                uploadFilename = session.get("%s.upload" % operation, None)
                                if validationIdentifier is None and not uploadIdentifier is None and not uploadFilename is None:
                                    validationIdentifier = uuid.uuid4().hex
                                    session["%s.validate" % operation] = validationIdentifier
                                    current_app.config["status"].update({validationIdentifier: {
                                        "status": "Queued for validation", "form": request.form}})
                                    current_app.config["queue"].put(
                                        (operation,session["uid"],uploadIdentifier, uploadFilename, validationIdentifier, request.form))
                                    current_app.config["logger"].debug("%s: queued %s for validation" % 
                                        (operation, uploadFilename,))
                            elif request.form["action"]=="download":
                                #locations
                                originalFilename = session.get("%s.upload" % operation, False)
                                validationIdentifier = session.get("%s.validate" % operation, False)
                                if originalFilename and validationIdentifier:
                                    validation = current_app.config["status"][validationIdentifier]
                                    validationStamp = "%s" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    if "ended" in validation:
                                        validationStamp = "%s" % datetime.datetime.fromtimestamp(
                                            validation["ended"]).strftime("%Y%m%d_%H%M%S")
                                    originalFilenameBase = originalFilename.rsplit(".", 1)[0]
                                    archiveDirectory = "%s_%s" % (originalFilenameBase,validationStamp)
                                    #checks
                                    if os.path.exists(uploadDirectory):
                                        uploadFilename = os.path.join(uploadDirectory,
                                                                      "%s" % session.get("%s.identifier" % operation, "unknown"))
                                        validationFilename = os.path.join(uploadDirectory,
                                                                      "%s" % session.get("%s.upload" % operation, "unknown"))
                                        if (os.path.exists(uploadFilename) and 
                                            os.path.exists(validationFilename)):
                                            #create archive
                                            mf = BytesIO()
                                            zf = zipfile.ZipFile(mf, mode="w")
                                            #add content
                                            zf.write(validationFilename, os.path.join(archiveDirectory,originalFilename))
                                            packageFilename = os.path.join(uploadDirectory, "%s.json" % validationIdentifier)
                                            if os.path.exists(packageFilename):
                                                zf.write(packageFilename, 
                                                         os.path.join(archiveDirectory,"%s.json" % originalFilenameBase))
                                            reportFilename = os.path.join(uploadDirectory, "%s.report.json" % validationIdentifier)
                                            if os.path.exists(reportFilename):
                                                zf.write(reportFilename, 
                                                         os.path.join(archiveDirectory,"%s.report.json" % originalFilenameBase))
                                            reportTextFilename = os.path.join(uploadDirectory, "%s.report.txt" % validationIdentifier)
                                            if os.path.exists(reportTextFilename):
                                                zf.write(reportTextFilename, 
                                                         os.path.join(archiveDirectory,"%s.report.txt" % originalFilenameBase))
                                            reportMarkdownFilename = os.path.join(uploadDirectory, "%s.report.md" % validationIdentifier)
                                            if os.path.exists(reportMarkdownFilename):
                                                zf.write(reportMarkdownFilename, 
                                                         os.path.join(archiveDirectory,"%s.report.md" % originalFilenameBase))
                                            zf.close()
                                            #output
                                            mf.seek(0)
                                            filename = "%s.zip" % originalFilenameBase
                                            response = make_response(mf.read())
                                            response.headers.set("Content-Type", "application/x-zip-compressed")
                                            response.headers.set("Content-Disposition", "attachment", filename=filename)
                                            return response
                    
                    #compute status
                    status = {
                        "upload": session.get("%s.upload" % operation, False),
                        "validation": None,
                    }
                    #try to add validation status
                    validationIdentifier = session.get("%s.validate" % operation, None)
                    if validationIdentifier and validationIdentifier in current_app.config["status"]:
                        status["validation"] = current_app.config["status"][validationIdentifier]
                    #final checks
                    if os.path.exists(uploadDirectory):
                        uploadFilename = os.path.join(uploadDirectory,"%s" % session.get("%s.identifier" % operation, "unknown"))
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
                            #try for report
                            if session.get("%s.validate" % operation, False) and "validation" in status:
                                if status["validation"].get("error", False):
                                    status["error"] = status["validation"]["error"]
                                    status["validation"].pop("error")
                                elif status["validation"].get("ended", False):
                                    reportFilename = os.path.join(uploadDirectory,"%s.report.json" % session.get("%s.validate" % operation))
                                    try:
                                        with open(reportFilename, "r") as report:
                                            status["report"] = json.load(report)
                                    except:
                                        status["report"] = None
                    else:
                        if session.get("%s.upload" % operation, False):
                            session.pop("%s.upload" % operation)
                        if session.get("%s.validate" % operation, False):
                            session.pop("%s.validate" % operation)
                    return jsonify(status)
                else:
                    validationConfigFilename = validator.Validate.getConfigFilename(self.config.get(operation,"config"))
                    variables["name"] = self.config.get(operation,"name",fallback=operation)
                    variables["download"] = self.config.getboolean(operation,"download",fallback=True)
                    variables["textUpload"] = self.config.get(operation,"text.upload",fallback="Select XLSX File for validation")
                    with open(validationConfigFilename, encoding="UTF-8") as configurationData:
                        validationConfig = json.load(configurationData)
                        variables["webinterface"] = validationConfig.get("webinterface",[])
                    return render_template("service.html", **variables)
            else:
                return redirect(url_for("index"))

        #start webservice
        host = self.config.get("webservice", "host", fallback="::")
        port = self.config.getint("webservice", "port", fallback=8080)
        threads = self.config.get("webservice", "threads", fallback=10) 
        self.logger.debug("start webservice on %s:%s with %s threads" % (host,port,threads))
        serve(app, host=host, port=port, threads=threads) 
        



