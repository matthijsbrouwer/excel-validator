$(function() {

    //initially hide all
    $(document).ready(function(){  
        $("div.form,div.status,div.validationSettings").hide();
        var urlStatus = $("body").data("url-status");
        $("input.delete").hide().on("click", function (e) {deleteEntry();});
        $("input.validate").hide().on("click", function (e) {validateEntry();});
        $("input.reset").hide().on("click", function (e) {resetEntry();});
        $("input.abort").hide().on("click", function (e) {abortEntry();});
        $("input.download").hide().on("click", function (e) {downloadEntry();});
        $.ajax({
          url: $("main").data("api"),  
          type: "get",
          data: {},
          success: function(data) {
              processData(data);
          }
        });
    });
    
    var Upload = function (file, inputObject, containerObject, errorObject) {
        this.file = file;
        this.url = $("main").data("api");
        this.input = inputObject;
        this.container = containerObject;
        this.error = errorObject;
    };
    
    Upload.prototype.getType = function() {
        return this.file.type;
    };
    Upload.prototype.getSize = function() {
        return this.file.size;
    };
    Upload.prototype.getName = function() {
        return this.file.name;
    };
    Upload.prototype.doUpload = function () {
        var that = this;
        var formData = new FormData();
        formData.append("file", this.file, this.getName()); 
        $.ajax({
            type: "POST",
            url: that.url,
            success: function (data) {
                that.input.val("");
                $("div.form").hide();
                processData(data);
            },
            error: function (error) {
                that.input.val("");
                //processData(data);
            },
            async: true,
            data: formData,
            cache: false,
            contentType: false,
            processData: false
        });
    };

    var deleteEntry = function() {
      $.ajax({
          type: "POST",
          url: $("main").data("api"),
          data: {"action": "delete"},  
          success: function(data) {
              processData(data);
          }
      });
    };

    var abortEntry = function() {
      $.ajax({
          type: "POST",
          url: $("main").data("api"),
          data: {"action": "abort"},  
          success: function(data) {
              processData(data);
          }
      });
    };

    var resetEntry = function() {
      $.ajax({
          type: "POST",
          url: $("main").data("api"),
          data: {"action": "reset"},  
          success: function(data) {
              processData(data);
          }
      });
    };

    var validateEntry = function() {
      let validateData = {"action": "validate"}
      $(".webinterfaceBlock input.form-check-input").each(function() {
          var oThis = $(this);
          let id = oThis.attr("id");
          let value = oThis.is(":checked") ? 1 : 0;
          validateData[id] = value;
      });
      $.ajax({
          type: "POST",
          url: $("main").data("api"),
          data: validateData,  
          success: function(data) {
              processData(data);
          }
      });
    };

    var checkStatus = function() {
      $.ajax({
          type: "GET",
          url: $("main").data("api"),
          success: function(data) {
              processData(data);
          }
      });
    };

    var downloadEntry = function() {
      var $form = $("<form>").attr("method", "post").attr("action", $("main").data("api"));
      var $hiddenField = $("<input/>").attr("type","hidden").attr("name", "action").val("download");
      $form.append($hiddenField);
      $("body").append( $form );
      $form.submit();
      $form.remove();
    }
    
    $("#formFile").on("change", function (e) {
        var file = $(this)[0].files[0];
        var containerObject = $(this).closest("div.form");
        var errorObject = $(this).closest("div.form").find("div.error");
        var upload = new Upload(file,$(this),containerObject,errorObject);
        upload.doUpload();
    });

    var processData = function(data) {
        if(!data.upload) {
            $("div.status").hide();
            $("div.validationSettings").hide();
            $("div.form").show();
            if(data.error) {
                $("div.error").text(data.error).show();
            } else {
                $("div.error").text("").hide();
            }   
        } else {
            $("div.form").hide();
            $("div.status").show();
            $("input.delete").show();
            $("div.status .uploadFilename").text(data.filename);
            $("div.status .uploadFilesize").text(Math.ceil(data.filesize/1024)+" kb");
            if(data.filetime) {
                let fileTime = new Date(data.filetime*1000);
                $("div.status .uploadFiletime").text(fileTime.toLocaleString());
            } else {
                $("div.status .uploadFiletime").text("---");
            }
            if(data.validation) {
                $("div.validationSettings").show();  
                $("div.validationSettings tr.value").each(function() {
                    var oThis = $(this);
                    let key = oThis.data("id");
                    oThis.find("td").removeClass("text-danger").removeClass("text-body-secondary");
                    if(key in data.validation.form) {
                        if(data.validation.form[key]=="0") {
                            oThis.find("th").html("-");
                            oThis.find("td").addClass("text-body-secondary");
                        } else if(data.validation.form[key]=="1") {
                            oThis.find("th").html("&#x2714;");
                            
                        } else {
                            oThis.find("th").text("???");
                            oThis.find("td").addClass("text-danger");
                        }
                    } else {
                        oThis.find("th").text("???");
                        oThis.find("td").addClass("text-danger");
                    }
                });
                if(!data.report && !data.error && data.validation.status) {
                    $("div.validation").show();
                    $("div.validation div.validationProgress").text(data.validation.status);
                    if(data.validation.total) {
                        let percentage = Math.ceil(100*data.validation.step/data.validation.total);
                        $("div.validation div.validationProgressBar").show();
                        $("div.validation div.validationProgressBar div.progress-bar").attr("aria-valuenow",percentage);
                        $("div.validation div.validationProgressBar div.progress-bar").css("width", percentage+"%");
                    } else {
                        $("div.validation div.validationProgressBar").hide();
                        $("div.validation div.validationProgressBar div.progress-bar").attr("aria-valuenow",0);
                        $("div.validation div.validationProgressBar div.progress-bar").css("width", "0%");
                    }
                } else {
                    $("div.validation").hide();
                    $("div.validation div.validationProgress").text("");
                }
                $("div.webinterface").hide();
                $("input.validate").hide();
                if(!data.report && !data.error) {
                    $("div.error").hide();
                    $("input.abort").show();
                    $("input.reset").hide();
                    $("input.download").hide();
                    setTimeout(function() {
    					checkStatus();
    				}, 1000);
    			} else {
                    $("input.reset").show();
                    $("input.abort").hide();
                    if(data.error) {
                        $("div.error").text(data.error).show();
                    } else {
                        $("div.error").text("").hide();
                    }
                    if(data.report) {
                        createReport(data.report);
                        $("div.report").show();
                        $("input.download").show();
                    } else {
                        $("div.report").text("").hide();
                        $("input.download").hide();
                    }
                }
            } else {
                $("div.validationSettings").hide();
                $("div.validation").hide();
                $("div.webinterface").show();
                $("input.validate").show();
                $("input.reset").hide();
                $("input.abort").hide();
                $("input.download").hide();
                if(data.error) {
                    $("div.error").text(data.error).show();
                } else {
                    $("div.error").text("").hide();
                }
                $("div.report").text("").hide();
            }
        }
    };

    var createReport = function(data) {
        $("div.report").text("");
        //content
        let content = $("<div class=\"accordion\"/>");
        //status
        let reportContent = $("<div class=\"accordion-item\"/>");
        let reportContentHeader = $("<h2 class=\"accordion-header d-flex lh-1\"/>");
        let reportContentHeaderText = $("<div class=\"accordion-body\"/>");
        reportContentHeader.append(reportContentHeaderText);
        reportContent.append(reportContentHeader);
        content.append(reportContent);
        //reports
        if(data.valid===true) {
            reportContentHeaderText.text("VALID");
            reportContent.addClass("bg-success").addClass("text-light");
        } else if(data.valid===false) {
            reportContentHeaderText.text("INVALID");
            reportContent.addClass("bg-danger").addClass("text-light");
        } else {
            reportContentHeaderText.text("UNKNOWN");
            reportContent.addClass("bg-warning").addClass("text-light");
        }
        let ignoreErrors = [];
        let ignoreWarnings = [];
        if(data.reports) {
            let naming = getNaming(data.reports);
            //create general
            let i = 0;
            while (i < data.reports.length) {
                let report = data.reports[i];
                if(report.reportType=="General") {
                    let reportContent;
                    [reportContent,ignoreErrors,ignoreWarnings] = createReportEntry(report,naming,ignoreErrors,ignoreWarnings);
                    content.append(reportContent);
                }
                i++;
            }
            //create resources
            i = 0;
            let resourceIndex = {};
            while (i < data.reports.length) {
                let report = data.reports[i];
                if(report.reportType=="Resource") {
                    let reportContent;
                    [reportContent,ignoreErrors,ignoreWarnings] = createReportEntry(report,naming,ignoreErrors,ignoreWarnings);
                    resourceIndex[data.reports[i].name] = reportContent;
                    content.append(reportContent);
                }
                i++;
            }
            //create resource transforms
            i = 0;
            while (i < data.reports.length) {
                let report = data.reports[i];
                if(report.reportType=="Resource Transform") {
                    let key = data.reports[i].parent.name;
                    if(key in resourceIndex) {
                        let reportContent = resourceIndex[key];
                        [ignoreErrors,ignoreWarnings] = updateReportEntryContent(
                            reportContent,data.reports[i],naming,ignoreErrors,ignoreWarnings);
                        showReportEntry(reportContent);
                    } else {
                        let reportContent;
                        [reportContent,ignoreErrors,ignoreWarnings] = createReportEntry(report,naming,ignoreErrors,ignoreWarnings);
                        content.append(reportContent);
                    }
                }
                i++;
            }
            //create package
            i = 0;
            while (i < data.reports.length) {
                let report = data.reports[i];
                if(report.reportType=="Package") {
                    let reportContent;
                    [reportContent,ignoreErrors,ignoreWarnings] = createReportEntry(report,naming,ignoreErrors,ignoreWarnings);
                    content.append(reportContent);
                }
                i++;
            }
        }
        //count
        let numberErrors = ignoreErrors.length;
        let numberWarnings = ignoreWarnings.length;
        if(numberErrors>0) {
            content.children().each(function() {
                let oThis = $(this);
                if(!oThis.data("errors")) {
                    oThis.show();
                } else if(oThis.data("errors").children().length>0) {
                    oThis.show();
                } else {
                    oThis.hide();
                }
            });
        } else if(numberErrors>0) {
            content.children().each(function() {
                let oThis = $(this);
                if(!oThis.data("warnings")) {
                    oThis.show();
                } else if(oThis.data("warnings").children().length>0) {
                    oThis.show();
                } else {
                    oThis.hide();
                }
            });
        }
        //buttons
        if(numberErrors>0||numberWarnings>0) {
            let control = $("<div class=\"d-flex flex-row-reverse\"/>");
            let controlButtons = $("<div class=\"btn-group btn-group-sm mb-2\"/>");
            controlButtons.append($("<span class=\"p-1 text-sm text-info\">details:</legend>"));
            let controlShow = $("<button class=\"btn btn-outline-info\" type=\"button\">show all</button>");
            controlShow.click(function () {$(".report-entry-content").collapse("show");});
            controlButtons.append(controlShow);
            let controlHide = $("<button class=\"btn btn-outline-info\" type=\"button\">hide all</button>");
            controlHide.click(function () {$(".report-entry-content").collapse("hide");});
            controlButtons.append(controlHide);
            control.append(controlButtons);
            $("div.report").append(control);
        }
        //add content
        $("div.report").append(content);

    };

    var createReportEntry = function(data,naming,ignoreErrors,ignoreWarnings) {
        let reportContent = $("<div class=\"accordion-item\"/>");
        let reportContentHeader = $("<h2 class=\"accordion-header d-flex lh-1\"/>");
        let reportContentHeaderButton = $("<button class=\"accordion-button collapsed me-auto\"/>");
        reportContentHeaderButton.attr("type","button");
        reportContentHeaderButton.attr("data-bs-toggle","collapse");
        reportContentHeaderButton.attr("data-bs-target","#reportContent_"+data.name);
        reportContentHeaderButton.attr("aria-expanded","false");
        reportContentHeaderButton.attr("aria-controls","#reportContent_"+data.name);
        if(data.reportType=="Resource") {
            reportContentHeaderButton.addClass("bg-light");
            reportContentHeaderButton.append($("<span/>").text("Sheet ["));
            reportContentHeaderButton.append($("<span/>").text(data.title).addClass("text-secondary"));
            reportContentHeaderButton.append($("<span/>").text("]"));
        } else if(data.reportType=="General") {
            reportContentHeaderButton.addClass("bg-light");
            reportContentHeaderButton.text(data.title);
        } else if(data.reportType=="Package") {
            reportContentHeaderButton.addClass("bg-light");
            reportContentHeaderButton.text(data.title);
        } else {
            reportContentHeaderButton.addClass("bg-light");
            reportContentHeaderButton.text(data.title);
        }
        let reportContentBadgeError = $("<span class=\"report-errors badge mx-2 text-bg-danger rounded-pill\"/>");
        let reportContentBadgeWarning = $("<span class=\"report-warnings badge mx-2 text-bg-warning rounded-pill\"/>");
        reportContentHeaderButton.append(reportContentBadgeError);
        reportContentHeaderButton.append(reportContentBadgeWarning);
        reportContentHeader.append(reportContentHeaderButton);
        reportContent.append(reportContentHeader);
        let reportContentContainer = $("<div class=\"report-entry-content accordion-collapse collapse\"/>");
        reportContentContainer.attr("id","reportContent_"+data.name);
        let reportContentBody = $("<div class=\"accordion-body\"/>");
        createReportEntryContent(reportContent,reportContentBody,data);
        [ignoreErrors,ignoreWarnings] = updateReportEntryContent(reportContent,data,naming,ignoreErrors,ignoreWarnings);
        reportContentContainer.append(reportContentBody);
        reportContent.append(reportContentContainer);
        showReportEntry(reportContent);
        return [reportContent,ignoreErrors,ignoreWarnings];
    };


    var getNaming = function(reports) {
        let i = 0;
        let naming = {};
        while (i < reports.length) {
            let report = reports[i];
            if(report.reportType=="Resource Transform") {
                naming[report.name] = {
                    "root": report.parent.name,
                    "title": report.parent.title
                }
            } else if(report.reportType=="Resource") {
                naming[report.name] = {
                    "root": report.name,
                    "title": report.title
                }
            }
            i+=1;
        }
        return naming;
    }

    var showReportEntry = function(reportContent) {
        let reportContentBadgeError = reportContent.find(".report-errors");
        let reportContentBadgeWarning = reportContent.find(".report-warnings");
        reportContentBadgeError.text("").hide();
        reportContentBadgeWarning.text("").hide();
        if(reportContent.data("errors").children().length>0 || reportContent.data("warnings").children().length>0) {
            reportContent.show();
            if(reportContent.data("errors").children().length==0) {
                reportContent.find(".errors").hide();
                reportContent.find(".warnings").show();
                reportContentBadgeWarning.text("warning");
                reportContentBadgeWarning.show();
            } else {
                reportContent.find(".warnings").hide();
                reportContent.find(".errors").show();
                reportContentBadgeError.text("error");
                reportContentBadgeError.show();
            }
        } else {
            reportContent.hide();
        }
    }

    var createReportEntryContent = function(container,entry,data) {
        let listErrors = $("<ol class=\"errors list-group\"/>");
        let listWarnings = $("<ol class=\"warnings list-group\"/>");
        entry.append(listErrors);
        entry.append(listWarnings);
        container.data("errors",listErrors);
        container.data("warnings",listWarnings);
    }

    var updateReportEntryContent = function(container,data,naming,ignoreErrors,ignoreWarnings) {
        let indexErrors = {};
        let indexWarnings = {};
        let listErrors = container.data("errors");
        let listWarnings = container.data("warnings");
        let frictionlessNumber = 10;
        if(data.errors) {
            let i = 0;
            while (i < data.errors.length) {
                if(!(data.errors[i][0] in indexErrors)) {
                    indexErrors[data.errors[i][0]] = $("<li class=\"list-group-item\"/>");
                    let listErrorEntryTitle = $("<div class=\"fw-bold\"/>");
                    listErrorEntryTitle.text(data.errors[i][0]);
                    indexErrors[data.errors[i][0]].append(listErrorEntryTitle);
                    listErrors.append(indexErrors[data.errors[i][0]]);
                }
                if(data.errors[i][1]) {
                    let listErrorEntryText = $("<div class=\"fw-light\"/>");
                    listErrorEntryText.text(data.errors[i][1]);
                    indexErrors[data.errors[i][0]].append(listErrorEntryText);
                }
                i++;
            }
        }
        if(data.warnings) {
            let i = 0;
            while (i < data.warnings.length) {
                if(!(data.warnings[i][0] in indexWarnings)) {
                    indexWarnings[data.warnings[i][0]] = $("<li class=\"list-group-item\"/>");
                    let listWarningEntryTitle = $("<div class=\"fw-bold\"/>");
                    listWarningEntryTitle.text(data.warnings[i][0]);
                    indexWarnings[data.warnings[i][0]].append(listWarningEntryTitle);
                    listWarnings.append(indexWarnings[data.warnings[i][0]]);
                }
                if(data.warnings[i][1]) {
                    let listWarningEntryText = $("<div class=\"fw-light\"/>");
                    listWarningEntryText.text(data.warnings[i][1]);
                    indexWarnings[data.warnings[i][0]].append(listWarningEntryText);
                }
                i++;
            }
        }
        if(data.frictionless) {
            if(!data.frictionless.valid) {
                let i = 0;
                while (i < data.frictionless.tasks.length) {
                    let task = data.frictionless.tasks[i];
                    if (!task.valid) {
                        let j = 0;
                        while (j < task.errors.length) {
                            let key = "frictionless-"+task.errors[j]["type"];
                            let title = task.errors[j]["title"];
                            if(data.reportType=="Resource" || data.reportType=="Resource Transform" || data.reportType=="Package") {
                                let taskKey = "resource:" + task.name;
                                if(taskKey in naming) {
                                    key = key + "-" + naming[taskKey].root;
                                    title = title + " - " + naming[taskKey].title;
                                } else {
                                    key = key + "-" + task.name;
                                    title = title + " - " + task.name;
                                }
                            } else {
                                key = key + "-" + task.name;
                            }
                            if(task.errors[j]["note"] && !(ignoreErrors.includes(key))) {
                                if(!(key in indexErrors)) {
                                    let listErrorEntry = $("<li class=\"list-group-item\"/>");
                                    let listErrorEntryTitle = $("<div class=\"fw-bold\"/>");
                                    listErrorEntryTitle.text(title);
                                    listErrorEntry.append(listErrorEntryTitle);
                                    let listErrorEntryDescription = $("<div class=\"fw-medium\"/>");
                                    listErrorEntryDescription.text(task.errors[j]["description"]);
                                    listErrorEntry.append(listErrorEntryDescription);
                                    indexErrors[key] = $("<ul class=\"list-group\"/>");
                                    listErrorEntry.append(indexErrors[key]);
                                    listErrors.append(listErrorEntry);
                                    indexErrors[key].data("number",0);
                                }
                                let number = indexErrors[key].data("number") + 1;
                                if(number<frictionlessNumber) {
                                    let listErrorEntryText = $("<li class=\"list-group-item list-group-item-action border-0 p-0 ps-1 small\"/>");
                                    let location = excelCoordinates(task.errors[j]);
                                    if(location && data.reportType!="Resource Transform") {
                                        let locationEntry = $("<span class=\"fw-bold pe-1\"/>");
                                        locationEntry.text(location);
                                        listErrorEntryText.append(locationEntry);
                                        if(task.errors[j]["fieldName"] && task.errors[j]["cell"]) {
                                            let cellEntry = $("<span class=\"fw-normal pe-1\"/>");
                                            cellEntry.text("("+task.errors[j]["fieldName"]+": "+task.errors[j]["cell"]+")");
                                            listErrorEntryText.append(cellEntry);
                                        }
                                        let sepEntry = $("<span class=\"fw-normal pe-1\"/>");
                                        sepEntry.text(":");
                                        listErrorEntryText.append(sepEntry);
                                    } else if(task.errors[j]["fieldName"] && task.errors[j]["cell"]) {
                                        let cellEntry = $("<span class=\"fw-normal pe-1\"/>");
                                        cellEntry.text("("+task.errors[j]["fieldName"]+": "+task.errors[j]["cell"]+")");
                                        listErrorEntryText.append(cellEntry);
                                        let sepEntry = $("<span class=\"fw-normal pe-1\"/>");
                                        sepEntry.text(":");
                                        listErrorEntryText.append(sepEntry);
                                    }
                                    let noteEntry = $("<span class=\"fw-light\"/>");
                                    noteEntry.text(task.errors[j]["note"]);
                                    listErrorEntryText.append(noteEntry);
                                    indexErrors[key].append(listErrorEntryText);
                                } else if (number==frictionlessNumber) {
                                    indexErrors[key].children().last().text("...");
                                }
                                indexErrors[key].data("number",number);
                            }
                            j++;
                        }
                    }
                    i++;
                }
            }
        }
        let newIgnoreErrors = Object.keys(indexErrors).concat(ignoreErrors);
        let newIgnoreWarnings = Object.keys(indexWarnings).concat(ignoreWarnings);
        return [newIgnoreErrors, newIgnoreWarnings];
    }

    var excelCoordinates = function(error) {
        row = error.rowNumber;
        column = error.fieldNumber;
        let LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        if(jQuery.type(column) !== "undefined") {
            result = [];
            while(column>0) {
                remainder = (column-1) % 26
                column = Math.floor((column-1) / 26)
                result.push(LETTERS.at(remainder));
            }
            let text = result.join("");
            if(jQuery.type(row) !== "undefined") {
                return text+row;
            } else {
                return "column "+text;
            }
        } else if(jQuery.type(row) !== "undefined") {
            return "row "+row;
        } else {
            return false;
        }
    }

});