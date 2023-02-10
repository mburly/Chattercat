if(document.cookie == "") {
    window.location.replace("index.html");
}

var state = "main";
var _name = "";
var _usage = "";
var _url = "";
var _path = "";
var _dateAdded = "";

window.onload = function() {
    startTime();
    loadStatus();
    loadAdmins();
    loadConsole();
	loadMainData();
    loadTools();
    init();
};
listeners();
setInterval(function(){
    loadMainData()
},5000);
// on focus, set window_focus = true.
$(window).focus(function() {
    window_focus = true;
});

// when the window loses focus, set window_focus to false
$(window).focusout(function() {
    window_focus = true;
});



class Counter {
	constructor(startDelay, endDelay) {
		this.startDelay = startDelay || 50;
		this.endDelay = endDelay || this.startDelay;
	}
	runCounter(objID, start, finish) {
		if (isNaN(start) || isNaN(finish)) {
			return;
		}
		if (finish - start === 0) {
			return;
		}
		const obj = document.getElementById(objID);
		let num = start;
		let delay = this.startDelay;
		let delayOffset = Math.floor((this.endDelay - this.startDelay) / (finish - start));
		let timerStep = function() {
			if (num <= finish) {
				obj.innerHTML = num.toLocaleString("en-US");
				delay += delayOffset;
				num += 1;
				setTimeout(timerStep, delay/7);
			}
		}
		timerStep();
	}
}


function loadConsole() {
    $.get("php/admin.php", function(data, status) {
        var data = JSON.parse(data);
        if(data["error"] != "") {
            window.location.replace("index.html");
        }
        for(let i = 0; i < data["numConsoleMessages"]; i++) {
            var name = "console " + i;
            var type = "[INFO]";
            if(data[name]["consoleType"] == 1) {
                type = "[INFO]";
            }
            else {
                type = "[ERROR]";
            }
            $('#console').append('<li><span class="console-datetime">' + data[name]["consoleDatetime"] + '</span> <span class="console-channel-name">' + data[name]["consoleChannel"] + '</span> <span class="console-message-type-info">' + type + '</span> <span class="console-message">' + data[name]["consoleMessage"] + '</span></li>');
        }
        remove("consoleLoad");
    });

}

function init() {
    $.get("php/validate.php", function(data, status) {
        var data = JSON.parse(data);
        if(data["error"] == "invalid token" || data["error"] == "token expired") {
            document.cookie = "cc_admin_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.replace("index.html");
        }
        else
        {
            callChannels();
            callAdmin();
        }
    });
    state = "adminContent";
}

function callAdmin() {
    $.get("php/admin.php", function(data, status) {
        var data = JSON.parse(data);
        if(data["executeStart"] == "") {
            $('#runtime').text('offline');
        }
        else {
            var datetime = data["executeStart"].split(' ');
            var d = new Date(datetime[0] + 'T' + datetime[1]).toString().split(' GMT')[0].slice(0,-3);
            $('#runtime').text(d);
        }
        remove("usernameLoader");
        $('.username').text(data["username"]);
        $('#emotesLogged').text(data["numEmotes"].toLocaleString("en-US"));
        $('#channelsTracked').text(data["numChannels"].toLocaleString("en-US"));
        $('#messagesLogged').text(data["numMessages"].toLocaleString("en-US"));
        $('#channelsTracking').text(data["numChannelsOnline"].toLocaleString("en-US"));
    });
}

function callChannels() {
    $.get("php/channels.php", function(data, status) {
        var data = JSON.parse(data);
        $('#streamsListTooltip').append('<strong>streams.txt</strong><ul>');
        for(let i = 0; i < data["streams"].length; i++) {
            var channelName = data["streams"][i];
            if(data["channels"].includes(channelName)) {
                $('#streamsListTooltip').append('<li class="stream-tracked"><i class="fas fa-check indicator"></i>' + channelName +'</li>');
            }
            else {
                $('#streamsListTooltip').append('<li class="stream-not-tracked"><i class="fas fa-xmark indicator"></i>' + channelName +'</li>');   
            }
        }
    });
}

function listeners() {
    $("body").on("mousedown", '.channel-select', function (e) {
        e.preventDefault();
        $('this').addClass("mouse-down");
    });

    $("body").on("mousedown", '#adminManageEmotesButton', function (e) {
        e.preventDefault();
        $(this).addClass("mouse-down");
    });

    $('body').on('click', '.title', function(){
        if(state != "adminContent") {
            remove(state);
            state = "adminContent";
            show(state);
        }
    });

    $('body').on('click','.logo', function(){
        window.location.href = $(this).attr('src');
    });
    
    $('body').on('click','#logout', function(){
        document.cookie = "cc_admin_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        window.location.href = "index.html";
    });
    
    $('body').on('click','#home', function(){
        window.location.href = "index.html";
    });
    
    $('body').on('click','#refresh', function(){
        location.reload(true);
    });

    $('body').on('click','#adminProfanityButton', function(){
    });

    $('body').on('click', '#adminManageEmotesButton', function() {
        if(state != "manageEmotesChannelSelect") {
            $.get("php/streams.php", function(data, status) {
                var data = JSON.parse(data);
                if(state == "adminContent") {
                    hide(state);
                }
                else {
                    remove(state);
                }
                $('#main').append('<div class="window" id="manageEmotesChannelSelect"><div class="title-bar window-blue"><div class="title-bar-text">Manage emotes - select a channel</div></div><div class="window-body"><ul class="admin-channel-list"></ul></div></div>');
                for(let i = 0; i < data["channels"].length; i++) {
                    $('.admin-channel-list').append('<li class="channel"><span class="channel-select" id="' + data["channels"][i] + '-channelSelect"><img class="channel-icon" src="' + data["pictures"][i] + '"><span class="channel-name">' + data["channels"][i] + '</span></span></li>')
                }
                state = "manageEmotesChannelSelect";
            });
        }
        else {
        }
    });

    $('body').on('click', '.channel-select', function() {
        var channel = $(this).attr('id').split('-')[0];
        if(state == "manageEmotesChannelSelect") {
            remove(state);
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "php/adminEmotes.php", false);
            xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
            var jsonPayload = '{"channel" : "' + channel + '"}';
            xhr.send(jsonPayload);
            var data = JSON.parse(xhr.responseText);
            $('body').append('<div class="window" id="adminManageEmotes"><div class="title-bar window-blue"><div class="title-bar-text">' + channel + ' - Manage Emotes</div></div><div class="window-body"><table class="admin-manage-emote-table" id="manageEmotesTable" style="background:#c6c6c6;"><tr id="manageEmotesHeaderRow"><th class="manage-emotes-col manage-emotes-emote-image-col"></th><th class="manage-emotes-col manage-emotes-emote-name-col">Name</th><th class="manage-emotes-col manage-emotes-emote-count-col">Usage</th><th class="manage-emotes-col manage-emotes-emote-url-col">URL</th><th class="manage-emotes-col manage-emotes-emote-path-col">Path</th><th class="manage-emotes-col manage-emotes-emote-date-col">Date added</th><th class="manage-emotes-col manage-emotes-emote-source-col">Source</th><th class="manage-emotes-col manage-emotes-emote-active-col">Active</th><th class="manage-emotes-col manage-emotes-emote-tools-col">Actions</th></tr>');
            for(let i = 0; i < data["codes"].length; i++) {
                var dateTemp = data["dates"][i].split('-');
                var date_addded = dateTemp[1] + '/' + dateTemp[2] + '/' + dateTemp[0];
                var source = "Twitch";
                var active = "Enabled";
                if(data["sources"][i] == 2) {
                    source = "Subscriber";
                }
                else if(data["sources"][i] == 3 || data["sources"][i] == 4) {
                    source = "FFZ";
                }
                else if(data["sources"][i] == 5 || data["sources"][i] == 6) {
                    source = "BTTV";
                }
                if(!data["active"][i]) {
                    active = "Disabled";
                }
                const imageCol = '<td class="manage-emotes-col manage-emotes-emote-image-col manage-emotes-emote-image"><div class="tooltip-top"><span class="tooltiptext"><img class="emote-tooltip" id="' + data["codes"][i] + '-tooltip" src="' + data["paths"][i] + '"></span><img class="channel-emote" src="' + data["paths"][i] + '"></div></td>';
                const nameCol = '<td class="manage-emotes-col manage-emotes-emote-name-col manage-emotes-emote-name emote-name">' + data["codes"][i] + '</td>';
                const countCol = '<td class="manage-emotes-col manage-emotes-emote-count-col manage-emotes-emote-count">' + data["counts"][i].toLocaleString('en-US') + '</td>';
                const urlCol = '<td class="manage-emotes-col manage-emotes-emote-url-col manage-emotes-emote-url"><a href="' + data["urls"][i] +'" title="' + data["urls"][i] + '">' + data["urls"][i] + '</a></td>';
                const pathCol = '<td class="manage-emotes-col manage-emotes-emote-path-col manage-emotes-emote-path" title="' + data["paths"][i] + '">' + data["paths"][i] + '</td>';
                const dateCol = '<td class="manage-emotes-col manage-emotes-emote-date-col manage-emotes-emote-date-added">' + date_addded + '</td>';
                const sourceCol = '<td class="manage-emotes-col manage-emotes-emote-source-col manage-emotes-emote-source ' + source + '-emote">' + source + '</td>';
                const activeCol = '<td class="manage-emotes-col manage-emotes-emote-active-col manage-emotes-emote-active emote-' + active + '" id="' + data["sources"][i] + '-' + data["emote_ids"][i] + '-active">' + active + '</td>';
                var toolsCol = ''; 
                if(active == "Enabled") {
                    toolsCol = '<td class="manage-emotes-col manage-emotes-emote-tools-col manage-emotes-tools"><span class="admin-tool edit-tool" id="' + channel + '-' + data["sources"][i] + '-' + data["emote_ids"][i] + '-editButton" title="edit this emote"><i class="fas fa-cog"></i></span><a class="download-emote-link" href="' + data["urls"][i] + '" download target="_blank"><span class="admin-tool download-tool" title="download this emote"><i class="fas fa-download"></i></a></span><span class="admin-tool disable-tool" id="' + channel + '-' + data["sources"][i] + '-' + data["emote_ids"][i] + '-disableButton" title="disable this emote"><i class="fas fa-cancel"></i></span><span class="admin-tool delete-tool" id="' + channel + '-' + data["sources"][i] + '-' + data["emote_ids"][i] + '-deleteButton" title="delete this emote"><i class="fas fa-x"></i></span></td>';
                }
                else {
                    toolsCol = '<td class="manage-emotes-col manage-emotes-emote-tools-col manage-emotes-tools"><span class="admin-tool edit-tool" id="' + channel + '-' + data["sources"][i] + '-' + data["emote_ids"][i] + '-editButton" title="edit this emote"><i class="fas fa-cog"></i></span><a class="download-emote-link" href="' + data["urls"][i] + '" download target="_blank"><span class="admin-tool download-tool" title="download this emote"><i class="fas fa-download"></i></a></span><span class="admin-tool enable-tool" id="' + channel + '-' + data["sources"][i] + '-' + data["emote_ids"][i] + '-enableButton" title="enable this emote"><i class="fas fa-check"></i></span><span class="admin-tool delete-tool" id="' + channel + '-' + data["sources"][i] + '-' + data["emote_ids"][i] + '-deleteButton" title="delete this emote"><i class="fas fa-x"></i></span></td>';
                }
                $('.admin-manage-emote-table').append('<tr class="manage-emote-row" id="' + data["sources"][i] + '-' +  data["emote_ids"][i] + '-manageRow">' + imageCol + nameCol + countCol + urlCol + pathCol + dateCol + sourceCol + activeCol + toolsCol + '</tr>');
            }
            state = "adminManageEmotes";
        }
    });

    $('body').on('click', '.disable-tool', function(){
        var id = $(this).attr('id').split('-');
        var channel = id[0];
        var source = id[1];
        var emote_id = id[2];
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "php/adminEmoteUpdate.php", false);
        xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
        var jsonPayload = '{"channel" : "' + channel + '","source" : ' + source + ',"emote_id" : "' + emote_id + '","new_value" : 0,"type" : "' + 'active"}';
        xhr.send(jsonPayload);
        id = $(this).attr('id').split('-');
        var channel = id[0];
        var source = id[1];
        var emote_id = id[2];
        var enableTool = '<span class="admin-tool enable-tool" id="' + channel + '-' + source + '-' + emote_id + '-enableButton" title="enable this emote"><i class="fas fa-check"></i></span>';
        $(this)[0].outerHTML = enableTool;
        var statusCol = '<td class="manage-emotes-col manage-emotes-emote-active-col manage-emotes-emote-active emote-Disabled" id="' + source + '-' + emote_id + '-active">Disabled</td>';
        var statusColId = source + '-' + emote_id + '-active';
        document.getElementById(statusColId).outerHTML = statusCol;
    });

    $('body').on('click', '.enable-tool', function(){
        var id = $(this).attr('id').split('-');
        var channel = id[0];
        var source = id[1];
        var emote_id = id[2];
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "php/adminEmoteUpdate.php", false);
        xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
        var jsonPayload = '{"channel" : "' + channel + '","source" : ' + source + ',"emote_id" : "' + emote_id + '","new_value" : 1,"type" : "' + 'active"}';
        xhr.send(jsonPayload);
        id = $(this).attr('id').split('-');
        var channel = id[0];
        var source = id[1];
        var emote_id = id[2];
        var disableTool = '<span class="admin-tool disable-tool" id="' + channel + '-' + source + '-' + emote_id + '-disableButton" title="disable this emote"><i class="fas fa-cancel"></i></span>';
        $(this)[0].outerHTML = disableTool; 
        var statusCol = '<td class="manage-emotes-col manage-emotes-emote-active-col manage-emotes-emote-active emote-Enabled" id="' + source + '-' + emote_id + '-active">Enabled</td>';
        var statusColId = source + '-' + emote_id + '-active';
        document.getElementById(statusColId).outerHTML = statusCol;
    });

    $('body').on('click', '.edit-tool', function(){
        var id = $(this).attr('id');
        var channel = id.split('-')[0];
        var rowId = id.split(channel + '-')[1].split('-editButton')[0] + '-manageRow';
        var fields = document.getElementById(rowId).children;
        for (let i = 0; i < fields.length; i++) {
            var field_text = fields[i].textContent;
            tag = fields[i].outerHTML;
            if(!isImageRow(tag) && !isToolsRow(tag) && !isSourceRow(tag) && !isActiveRow(tag)) {
                if(isNameRow(tag)) {
                    _name = fields[i].textContent;
                }
                else if(isUsageRow(tag)) {
                    _usage = parseInt(fields[i].textContent);
                }
                else if(isUrlRow(tag)) {
                    _url = fields[i].textContent;
                }
                else if(isPathRow(tag)) {
                    _path = fields[i].textContent;
                }
                else if(isDateRow(tag)) {
                    _dateAdded = fields[i].textContent;
                }
                fields[i].textContent = '';
                tag = fields[i].outerHTML;
                var new_tag = tag.replaceAll('td', 'input');
                fields[i].outerHTML = new_tag;
                fields[i].value = field_text;
            }
            else if(isToolsRow(tag)) {
                var editCompleteTool = '<span class="admin-tool edit-complete-tool" id="' + id.split('-editButton')[0] + '-editCompleteTool" title="finish changes"><i class="fas fa-check"></i></span>';
                if(isEmoteEnabled(fields[i].outerHTML)) {
                    var editTool = fields[i].outerHTML.split('<td class="manage-emotes-col manage-emotes-emote-tools-col manage-emotes-tools">')[1].split('<a')[0];
                }
                else {
                    var editTool = fields[i].outerHTML.split('<td class="manage-emotes-col manage-emotes-emote-tools-col manage-emotes-tools">')[1].split('<span class="admin-tool download-tool" title="download this emote">')[0];
                }
                fields[i].outerHTML = fields[i].outerHTML.replace(editTool, editCompleteTool);
            }
        }
    });

    $('body').on('click', '.edit-complete-tool', function() {
        var id = $(this).attr('id');
        var channel = id.split('-')[0];
        var source = id.split('-')[1];
        var emote_id = id.split('-')[2];
        var rowId = id.split(channel + '-')[1].split('-editCompleteTool')[0] + '-manageRow';
        var fields = document.getElementById(rowId).children;
        var numChanges = 0;
        var changes = '{"channel":"' + channel + '","source":' + source + ',"emote_id":"' + emote_id + '",';
        for (let i = 0; i < fields.length; i++) {
            var tag = fields[i].outerHTML;
            if(isNameRow(tag)) {
                if(fields[i].value != _name) {
                    changes += '"code":"' + fields[i].value + '",';
                    numChanges += 1;
                }
            }
            else if(isUsageRow(tag)) {
                if(parseInt(fields[i].value) != _usage) {
                    changes += '"count":' + fields[i].value + ',';
                    numChanges += 1;
                }
            }
            else if(isUrlRow(tag)) {
                if(fields[i].value != _url) {
                    changes += '"url":"' + fields[i].value + '",';
                    numChanges += 1;
                }
            }
            else if(isPathRow(tag)) {
                if(fields[i].value != _path) {
                    changes += '"path":"' + fields[i].value + '",';
                    numChanges += 1;
                }
            }
            else if(isDateRow(tag)) {
                if(fields[i].value != _dateAdded) {
                    changes += '"date":"' + fields[i].value + '",';
                    numChanges += 1;
                }
            }
        }
        if(numChanges > 0) {
            changes = changes.slice(0, -1);
            if(numChanges == 1) {
                // php emote single update 
                // adminEmoteUpdate.php

                var column = changes.split(',')[3].split(':')[0];
                changes = changes.replace(column, "\"new_value\"");
                changes += ',"type":"' + column.replaceAll('\"',"") + '"}';
                var xhr = new XMLHttpRequest();
                xhr.open("POST", "php/adminEmoteUpdate.php", false);
                xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
                xhr.send(changes);
            }
            else {
                // php emote multiple updates
            }
        }

        var fields = document.getElementById(rowId).children;
        for (let i = 0; i < fields.length; i++) {
            tag = fields[i].outerHTML;
            if(!isImageRow(tag) && !isToolsRow(tag) && !isSourceRow(tag) && !isActiveRow(tag)) {
                var value = fields[i].value;
                var new_tag = tag.replaceAll('input', 'td');
                fields[i].outerHTML = new_tag;
                fields[i].textContent = value;
            }
            else if(isToolsRow(tag)) {
                var editTool = '<span class="admin-tool edit-tool" id="' + channel + '-' + source + '-' + emote_id + '-editButton" title="edit this emote"><i class="fas fa-cog"></i></span>';
                if(isEmoteEnabled(fields[i].outerHTML)) {
                    var editCompleteTool = fields[i].outerHTML.split('<td class="manage-emotes-col manage-emotes-emote-tools-col manage-emotes-tools">')[1].split('<a')[0];
                }
                else {
                    var editCompleteTool = fields[i].outerHTML.split('<td class="manage-emotes-col manage-emotes-emote-tools-col manage-emotes-tools">')[1].split('<span class="admin-tool download-tool"')[0];
                }
                fields[i].outerHTML = fields[i].outerHTML.replace(editCompleteTool, editTool);
            }
        }

    });

    $('body').on('click', '.delete-tool', function() {
        var id = $(this).attr('id').split('-');
        var channel = id[0];
        var source = id[1];
        var emote_id = id[2];
        var jsonPayload = '{"channel":"' + channel + '","source":' + source + ',"emote_id":"' + emote_id + '"}';
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "php/adminEmoteDelete.php", false);
        xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
        xhr.send(jsonPayload);
        console.log(xhr.responseText);
        var rowId = $(this).attr('id').split(channel + '-')[1].split('-deleteButton')[0] + '-manageRow';
        remove(rowId);
    });

}

function loadMainData() {
    $.get("php/validate.php", function(data, status) {
        var data = JSON.parse(data);
        if(data["error"] == "invalid token" || data["error"] == "token expired") {
            document.cookie = "cc_admin_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.replace("index.html");
        }
        else
        {
            $.get("php/admin.php", function(data, status) {
                var data = JSON.parse(data);
                $('.username').text(data["username"]);
                $('#emotesLogged').text(data["numEmotes"].toLocaleString("en-US"));
                $('#channelsTracked').text(data["numChannels"].toLocaleString("en-US"));
				var oldNum = parseInt(document.getElementById('messagesLogged').innerHTML.replaceAll(",",""));
				let countUp = new Counter();
				countUp.runCounter("messagesLogged",oldNum,data["numMessages"]);				
                $('#channelsTracking').text(data["numChannelsOnline"].toLocaleString("en-US"));
            });

        }
    });
}

function loadAdmins() {
    $.get("php/admins.php", function(data, status){
        var data = JSON.parse(data);
        for(let i = 0; i < data["usernames"].length; i++) {
            if(data["roles"][i] == 1) {
                $('.admin-list').append('<li class="admin"><img src="images/user_offline.gif" title="user is offline"><img src="images/super-admin-icon.png" title="Super Admin"><span class="admin-name">' + data["usernames"][i] + '</span></li>');
            }
            else {
                $('.admin-list').append('<li class="admin"><img src="images/user_offline.gif" title="user is offline"><img src="images/admin-icon.png" title="Admin"><span class="admin-name">' + data["usernames"][i] + '</li>');
            }
        }
    });
    remove('adminLoader');
}

function loadStatus() {
    $.get("php/status.php", function(data, status) {
        var data = JSON.parse(data);
        if(data["status"] == "online") {
            remove("statusLoader");
            $('#statusContainer').append('<span class="status online">online</span>');
        }
        else {
            remove("statusLoader");
            $('#statusContainer').append('<span class="status offline">offline</span>');
        }
    });
}

function loadTools() {
    $('#content-admin').append('<span class="admin-title"><img class="admin-tools-icon" src="images/admin-tools-icon.png"><span class="admin-title-text">Admin Actions</span></span><ul class="actions-list"><li class="admin-button"><button class="admin-action-button" id="adminProfanityButton">Profanity</button></li><li class="admin-button"><button class="admin-action-button" id="adminChannelsButton">Manage channels</button></li><li class="admin-button"><button class="admin-action-button" id="adminUsersButton">Manage users</button></li><li class="admin-button"><button class="admin-action-button" id="adminArchiveButton">Archive database</button></li></ul>');
}

function hide(id) {
    $('#' + id).css("display", "none");
}

function remove(id) {
	try {
		document.getElementById(id).remove();
	}
	catch(err) {
		console.log(err);
	}
}

function show(id) {
    $('#' + id).css("display", "block");
}

function isImageRow(html) {
    return html.split('manage-emotes-emote-image').length > 1;
}

function isNameRow(html) {
    return html.split('manage-emotes-emote-name').length > 1;
}

function isUsageRow(html) {
    return html.split('manage-emotes-emote-count').length > 1;
}

function isUrlRow(html) {
    return html.split('manage-emotes-emote-url').length > 1;
}

function isPathRow(html) {
    return html.split('manage-emotes-emote-path').length > 1;
}

function isDateRow(html) {
    return html.split('manage-emotes-emote-date-added').length > 1;
}

function isToolsRow(html) {
    return html.split('manage-emotes-tools').length > 1;
}

function isActiveRow(html) {
    return html.split('manage-emotes-emote-active').length > 1;
}

function isSourceRow(html) {
    return html.split('manage-emotes-emote-source').length > 1;
}

function isEmoteEnabled(html) {
    return html.split('disable this emote').length > 1;
}

function startTime() {
    const today = new Date();
    let h = today.getUTCHours();
    let m = today.getUTCMinutes();
    let s = today.getUTCSeconds();
    m = checkTime(m);
    s = checkTime(s);
    document.getElementById('clock').innerHTML =  h + ":" + m + ":" + s;
    setTimeout(startTime, 1000);
  }
  
function checkTime(i) {
if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
return i;
}
