$(function() {

    //initially hide all
    $(document).ready(function(){  
        $("div.form,div.status").hide();
        var urlStatus = $("body").data("url-status");
        $("input.delete").on("click", function (e) {deleteEntry();});
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
        console.log(this.url);
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
            processData: false,
            timeout: 600000
        });
    };

     var deleteEntry = function(id) {
      $.ajax({
          type: "POST",
          url: $("main").data("api"),
          data: {"action": "delete"},  
          success: function(data) {
              processData(data);
          }
      });
    };
    
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
            $("div.form").show();
        } else {
            $("div.form").hide();
            $("div.status").show();
            $("div.status .uploadFilename").text(data.filename);
            $("div.status .uploadFilesize").text(data.filesize);
            $("div.status .uploadFiletime").text(data.filetime);
        }
    };

});