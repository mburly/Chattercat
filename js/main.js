var state = "main";

loadStatus();
callIndex();
listeners();

function appendButtons(id)
{
    var channel = id.split('-')[0];
    $('#' + id).append('<li><div class="action-group"><button class="channel-emotes-button" id="' + channel + '-ChannelEmotesButton">View ' + channel + '\'s emotes</button></div></li>');
}

function callChannelEmotes(channel, data) {

}

function callIndex() {
    document.body.scrollTop = document.documentElement.scrollTop = 0;
    $.get("php/index.php", function(data, status) {
        var data = JSON.parse(data);
        hide("mainLoad");
        for(let i = 0; i < data["channels"].length; i++)
        {
            var channelName = data["channels"][i];
            var selectId = channelName + '-select';
            var infoId = channelName + '-info';
            if(data["live"][i] == true)
            {
                var streamStartDatetime = data[channelName]["streamStartDate"].split(' ');
                var streamStart = new Date(streamStartDatetime[0] + "T" + streamStartDatetime[1] + "Z");  // passing in ISO 8601 format
                var now = new Date();
                $('.channels').append('<li class="channel" id="channel-' + channelName + '"><span class="channel-select" id="' + selectId + '"><img class="channel-icon" src="pictures/' + channelName + '.png"><span class="channel-name live-channel" id="' + channelName + '-channelName">' + channelName + '</span></span><div class="selector main-selector" id="' + channelName + '-selector"></div></li>');
                $('.channels').append('<ul class="channel-info" id="' + infoId + '" style="display:none;"><li><span class="stream-title">' + data[channelName]['title'] + '</span></li>');
                $('#' + infoId).append('<li class="stream-info"><span class="info-property">Time live:</span><span class="info-value">' + msToTime(now-streamStart) + '</span></li>');
                $('#' + infoId).append('<li class="stream-info"><span class="info-property">Category:</span><span class="info-value">' + data[channelName]['category'] + '</span></li>');
                $('#' + infoId).append('<li class="stream-info"><span class="info-property">Messages sent:</span><span class="info-value">' + data[channelName]['numMessages'].toLocaleString("en-US") + '</span></li>');
                $('#' + infoId).append('<li class="stream-info"><span class="info-property">Unique chatters:</span><span class="info-value">' + data[channelName]['numChatters'].toLocaleString("en-US") + '</span></li>');
                $('#' + infoId).append('<li class="stream-info"><span class="info-property">New chatters:</span><span class="info-value">' + data[channelName]['newChatters'].toLocaleString("en-US") + '</span></li>');
                $('#' + infoId).append('</ul>');
                appendButtons(infoId);
            }
            else
            {
                $('.channels').append('<li class="channel" id="channel-' + channelName + '"><span class="channel-select" id="' + selectId + '"><img class="channel-icon" src="pictures/' + channelName + '.png"><span class="channel-name">' + channelName + '</span></span></li>');
            }
        }
    });
}

function listeners() {
    $('body').on('click','.title',function(){
        if(state == "main") {
        }
        else {
            remove(state);
            document.body.scrollTop = document.documentElement.scrollTop = 0;
            show("main");
            state = "main";
            document.title = "Home - Chattercat"
        }
    });
    
    $('body').on('click','.main-selector',function(){
        var id = $(this).attr('id').split('-')[0];
        if($('#' + id + '-info').css("display") == "none")
        {
            show(id + '-info');
            $(this).css("background-image","url('images/button-down.svg')");
        }
        else
        {
            hide(id + '-info');
            $(this).css("background-image","url('images/button-right.svg')");
        }
    });
    
    $('body').on('click','.session-selector',function(){
        var id = $(this).attr('id') + '-info';
        if($('#' + id).css("display") == "none")
        {
            show(id);
            $(this).css("background-image","url('images/button-down.svg')");
        }
        else
        {
            hide(id);
            $(this).css("background-image","url('images/button-right.svg')");
        }
    });
    
    $('body').on('click','.channel-select',function(){
        var id = $(this).attr('id').split('-')[0];
        loadChannelPage(id);
        state = "statsPage";
    });
    
    $('body').on('click','#mainExpandButton',function(){
        $('.channel-info').css("display", "block");
        $('.main-selector').css("background-image","url('images/button-down.svg')");
    });
    
    $('body').on('click','#mainCollapseButton',function(){
        $('.channel-info').css("display", "none");
        $('.main-selector').css("background-image","url('images/button-right.svg')")
    });
    
    $('body').on('click','#mainRefreshButton',function(){
        location.reload(true);
    });
    
    $('body').on('click','#sessionsExpandButton',function(){
        $('.session-info').css("display", "block");
        $('.session-selector').css("background-image","url('images/button-down.svg')")
    });
    
    $('body').on('click','#sessionsCollapseButton',function(){
        $('.session-info').css("display", "none");
        $('.session-selector').css("background-image","url('images/button-right.svg')")
    });
    
    $('body').on('click','.window-full-image',function(){
        window.location.href = $(this).attr("src");
    });
    
    $('body').on('click','.emote-tooltip',function(){
        var url = $(this).attr('src');
        window.open(url, '_blank');
    });
    
    $('body').on('click','.login-icon',function(){
        if(document.cookie == '') {
            showLoginPage();
        }
        else {
            $.get("php/validate.php", function(data, status) {
                if(data == "") {
                    showLoginPage();
                    return;
                }
                var data = JSON.parse(data);
                if(data["error"] == "invalid token") {
                    document.cookie = "cc_admin_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                    showLoginPage();
                }
                else
                {
                    if(data["error"] == "no login") {
                        showLoginPage();
                    }
                    else {
                        window.location.href = "housekeeping.html";
                    }
                }
            });
        }
    });
    
    $('body').on('click','#loginButton',function(){
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "php/login.php", false);
        xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
        var jsonPayload = '{"username" : "' + $('#username').val() + '","password" : "' + $('#password').val() + '"}';
        try {
            xhr.send(jsonPayload);
            var data = JSON.parse(xhr.responseText);
            if(data["error"] != "")
            {
                show('badLoginText');
            }
            else
            {
                window.location.href = "housekeeping.html";
            }
        }
        catch(err) {
            console.log(err);
        }
    
    });
    
    $('body').on('click', '.channel-emotes-button',function() {
        var channel = $(this).attr('id').split('-')[0];
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "php/emotes.php", false);
        xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
        var jsonPayload = '{"channel":"' + channel + '"}';
        xhr.send(jsonPayload);
        var data = JSON.parse(xhr.responseText);
        if(state == 'main') {
            hide(state);
        }
        else {
            remove(state);
        }
        $('body').append('<div id="channelEmotes"><div class="window" id="channelEmotesWindow"><div class="title-bar"><div class="title-bar-text">' + channel + ' - Emotes</div></div><div class="window-body"><ul class="channel-emotes">');
        for(let i = 0; i < data["codes"].length; i++) {
            var source = "Twitch";
            if(data["sources"][i] == 2) {
                source = "Subscriber";
            }
            else if(data["sources"][i] == 3 || data["sources"][i] == 4) {
                source = "FFZ";
            }
            else if(data["sources"][i] == 5 || data["sources"][i] == 6) {
                source = "BTTV";
            }
            $('.channel-emotes').append('<li class="channel-emotes-list-emote"><div class="channel-emote-holder"><div class="tooltip-top"><img class="channel-emote channel-emote-image" src="' + data["paths"][i] + '"><span class="tooltiptext"><img class="emote-tooltip" id="' + data["codes"]["i"] + '-tooltip" src="' + data["paths"][i] + '"></span></div><span class="channel-emote-name" title="' + data["codes"][i] + '">' + data["codes"][i] + '</span><span class="channel-emote-type ' + source + '-emote" style="margin-top:5px;">' + source + '</span></div></li>');
        }
        state = "channelEmotes";
    });

    $('body').on("mousedown", '.channel-name', function (e) {
        e.preventDefault();
        $(this).addClass("mouse-down");
    });

    $('body').on('click', '.info-help-hide', function() {
        remove('infoHelp');
    });
}

function loadChannelPage(id)
{
    document.body.scrollTop = document.documentElement.scrollTop = 0;
    var channel = id.split("-")[0];
    var xhr = new XMLHttpRequest();
	xhr.open("POST", "php/stats.php", false);
	xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
    var jsonPayload = '{"channel" : "' + channel + '"}';
    try {
        xhr.send(jsonPayload);
        var data = JSON.parse(xhr.responseText);
        hide("main");
        document.title = channel + " - Chattercat"

        generateChannelPage(channel);

        var log_xhr = new XMLHttpRequest();
        log_xhr.open("POST", "php/updates.php", false);
        log_xhr.setRequestHeader("Content-type", "application/json; charset=UTF-8");
        var jsonPayload = '{"channel" : "' + channel + '"}';
        log_xhr.send(jsonPayload);
        if(log_xhr.responseText == "") {
            $('.emote-log').append('<div class="no-updates-text">No updates</div>');
        }
        else {
            var log_data = JSON.parse(log_xhr.responseText);
            for(let i = 0; i < 20; i++) {
                var id = 'log-' + i;
                if(log_data[id] == null) {
                    break;
                }
                var date = log_data[id]["datetime"].split(' ')[0].split('-');
                date = date[1].replace('0','') + '/' + date[2].replace('0','') + '/' + date[0];
                if(i == 0) {
                    if(log_data[id]["type"] == "disabled") {
                        $('.emote-log').append('<li class="log-item"><span class="badge log-date">' + date +'</span><img class="channel-icon log-icon" src="pictures/' + channel + '.png"><span class="channel-name log-channel-name">' + channel + '</span><span class="log-type text-disabled">disabled</span><div class="tooltip-bottom"><img class="emote log-emote" src="' + log_data[id]["path"] +'"><span class="tooltiptext"><img class="emote-tooltip" id="' + log_data[id]["path"] + '-tooltip" src="' + log_data[id]["path"] + '"></span></div><span class="emote-name log-emote-name">' + log_data[id]["emote"] +'</span></li>');
                    }
                    else if(log_data[id]["type"] == "enabled") {
                        $('.emote-log').append('<li class="log-item"><span class="badge log-date">' + date +'</span><img class="channel-icon log-icon" src="pictures/' + channel + '.png"><span class="channel-name log-channel-name">' + channel + '</span><span class="log-type text-enabled">enabled</span><div class="tooltip-bottom"><img class="emote log-emote" src="' + log_data[id]["path"] +'"><span class="tooltiptext"><img class="emote-tooltip" id="' + log_data[id]["path"] + '-tooltip" src="' + log_data[id]["path"] + '"></span></div><span class="emote-name log-emote-name">' + log_data[id]["emote"] +'</span></li>');
                    }
                    else {
                        $('.emote-log').append('<li class="log-item"><span class="badge log-date">' + date +'</span><img class="channel-icon log-icon" src="pictures/' + channel + '.png"><span class="channel-name log-channel-name">' + channel + '</span><span class="log-type text-reactivated">reactivated</span><div class="tooltip-bottom"><img class="emote log-emote" src="' + log_data[id]["path"] +'"><span class="tooltiptext"><img class="emote-tooltip" id="' + log_data[id]["path"] + '-tooltip" src="' + log_data[id]["path"] + '"></span></div><span class="emote-name log-emote-name">' + log_data[id]["emote"] +'</span></li>');
                    }
                }
                else {
                    if(log_data[id]["type"] == "disabled") {
                        $('.emote-log').append('<li class="log-item"><span class="badge log-date">' + date +'</span><img class="channel-icon log-icon" src="pictures/' + channel + '.png"><span class="channel-name log-channel-name">' + channel + '</span><span class="log-type text-disabled">disabled</span><div class="tooltip-top"><img class="emote log-emote" src="' + log_data[id]["path"] +'"><span class="tooltiptext"><img class="emote-tooltip" id="' + log_data[id]["path"] + '-tooltip" src="' + log_data[id]["path"] + '"></span></div><span class="emote-name log-emote-name">' + log_data[id]["emote"] +'</span></li>');
                    }
                    else if(log_data[id]["type"] == "enabled") {
                        $('.emote-log').append('<li class="log-item"><span class="badge log-date">' + date +'</span><img class="channel-icon log-icon" src="pictures/' + channel + '.png"><span class="channel-name log-channel-name">' + channel + '</span><span class="log-type text-enabled">enabled</span><div class="tooltip-top"><img class="emote log-emote" src="' + log_data[id]["path"] +'"><span class="tooltiptext"><img class="emote-tooltip" id="' + log_data[id]["path"] + '-tooltip" src="' + log_data[id]["path"] + '"></span></div><span class="emote-name log-emote-name">' + log_data[id]["emote"] +'</span></li>');
                    }
                    else {
                        $('.emote-log').append('<li class="log-item"><span class="badge log-date">' + date +'</span><img class="channel-icon log-icon" src="pictures/' + channel + '.png"><span class="channel-name log-channel-name">' + channel + '</span><span class="log-type text-reactivated">reactivated</span><div class="tooltip-top"><img class="emote log-emote" src="' + log_data[id]["path"] +'"><span class="tooltiptext"><img class="emote-tooltip" id="' + log_data[id]["path"] + '-tooltip" src="' + log_data[id]["path"] + '"></span></div><span class="emote-name log-emote-name">' + log_data[id]["emote"] +'</span></li>');
                    }
                }
                
            }
        }
        
        $('#chattersTitleBarText').append(channel + ' - Chatters');
        $('#emotesTitleBarText').append(channel + ' - Emotes');
        $('#messagesTitleBarText').append(channel + ' - Messages');
        $('#sessionsTitleBarText').append(channel + ' - Sessions');

        const chattersHead = '<div class="list-group-header">Top Chatters</div>';
        $('#chattersWindowBody').append(chattersHead);
        $('#chattersWindowBody').append('<ul id="chatterLeaderboard">');
        for(let i = 0; i < data["topChatterNames"].length; i++)
        {
            if(i == 0)
            {
                $('#chatterLeaderboard').append('<li class="rank"><span class="rank-number rank-1">1</span><span class="rank-1 rank-name"><span class="chatter-name">' + data["topChatterNames"][i] + '</span></span><span class="top-rank">' + data["topChatterCounts"][i].toLocaleString("en-US") + "</span></li>");
            }
            else if(i == 1)
            {
                $('#chatterLeaderboard').append('<li class="rank"><span class="rank-number rank-2">2</span><span class="rank-2 rank-name"><span class="chatter-name">' + data["topChatterNames"][i] + '</span></span><span class="top-rank">' + data["topChatterCounts"][i].toLocaleString("en-US") + "</span></li>");
            }
            else if(i == 2)
            {
                $('#chatterLeaderboard').append('<li class="rank"><span class="rank-number rank-3">3</span><span class="rank-3 rank-name"><span class="chatter-name">' + data["topChatterNames"][i] + '</span></span><span class="top-rank">' + data["topChatterCounts"][i].toLocaleString("en-US") + "</span></li>");
            }
            else
            {
                $('#chatterLeaderboard').append('<li class="rank"><span class="rank-number">' + (i+1) + '</span><span class="rank-name"><span class="chatter-name">' + data["topChatterNames"][i] + "</span></span><span>" + data["topChatterCounts"][i].toLocaleString("en-US") + "</span></li>");
            }
        }
        $('#chattersWindowBody').append('<div class="list-group" id="recentChattersListGroup">');
        $('#recentChattersListGroup').append('<div class="list-group-header">Recent Chatters</div>');
        var groupCounter = 1;
        for(let i = 0; i < data["recentChatterNames"].length; i++)
        {
            if(i % 3 == 0)
            {
                if(i == 0)
                {
                    $('#recentChattersListGroup').append('<ul class="recent-chatters" id="recentChat' + groupCounter + '">');
                }
                else
                {
                    $('#recentChattersListGroup').append('</ul>');
                    groupCounter += 1;
                    $('#recentChattersListGroup').append('<ul class="recent-chatters" id="recentChat' + groupCounter + '">');
                }
            }
            $('#recentChat' + groupCounter).append('<li class="chatter-name">' + data["recentChatterNames"][i] + '</li>');
        }
        $('#chattersWindowBody').append('</ul>');
        $('#chattersWindowBody').append('</div>');
        $('#chattersWindowBody').append('</div>');
        $('#chattersStatusBar').append('<p class="status-bar-field"><span class="status-bar-right">Total chatters: ' + data["totalChatters"].toLocaleString("en-US") + '</span></p>')
        hide("chattersLoad");


        const emotesHead = '<div class="list-group-header">Top Emotes</div>';
        $('#emotesWindowBody').append(emotesHead);
        $('#emotesWindowBody').append('<ul id="topEmotesList">');
        var source = "Twitch";
        for(let i = 0; i < data["topEmotePaths"].length; i++)
        {
            if(data["topEmoteSources"][i] == 2) {
                source = "Subscriber";
            }
            else if(data["topEmoteSources"][i] == 3 || data["topEmoteSources"][i] == 4) {
                source = "FFZ";
            }
            else if(data["topEmoteSources"][i] == 5 || data["topEmoteSources"][i] == 6) {
                source = "BTTV";
            }
            $('#topEmotesList').append('<li class="emote-item"><span class="emote-source ' + source + '-emote">' + source + '</span><div class="tooltip-top"><img class="emote" src="' + data["topEmotePaths"][i] + '"><span class="tooltiptext"><img class="emote-tooltip" id="' + data["topEmoteCodes"][i] + '-tooltip" src="' + data["topEmotePaths"][i] + '"></span></div><div class="emote-name-section"><span class="emote-name">' + data["topEmoteCodes"][i] + '</span></div><span class="emote-count">' + data["topEmoteCounts"][i].toLocaleString("en-US") + '</span></li>');
        }
        $('#emotesWindowBody').append('<button class="channel-emotes-button" id="' + channel + '-ChannelEmotesButton">View ' + channel + '\'s emotes</button>');
        $('#emotesStatusBar').append('<p class="status-bar-field"><span class="status-bar-right">Total emotes: ' + data["totalEmotes"].toLocaleString("en-US") + '</span></p>');
        hide("emotesLoad");


        $('#messagesWindowBody').append('<div class="list-group-header">Recent Messages</div>');
        $('#messagesWindowBody').append('<ul id="recentMessagesList">');
        for(let i = 0; i < data["recentMessageMessages"].length; i++)
        {
            var recentMessageDatetime = data["recentMessageDatetimes"][i].split(' ');
            var recentMessageTime = new Date(recentMessageDatetime[0] + "T" + recentMessageDatetime[1] + "Z");
            $('#recentMessagesList').append('<li class="recent-messages"><span class="message-time">' + milToTime(recentMessageTime) + '</span><span class="message-name chatter-name">' + data["recentMessageNames"][i] + '</span>:<span class="message-message">' + data["recentMessageMessages"][i] + '</span></li>');
        }
        if(data["recentSessionLengths"][0] == "null")
        {
            $('#messagesStatusBar').append('<p class="status-bar-field"><span class="status-bar-right">Messages this session: ' + data["recentSessionMessages"].toLocaleString("en-US") + '</span></p>');
            $('#messagesStatusBar').append('<p class="status-bar-field"><span class="status-bar-right">Total messages: ' + data["totalMessages"].toLocaleString("en-US") + '</span></p>');
                
        }
        else
        {
            $('#messagesStatusBar').append('<p class="status-bar-field"><span class="status-bar-right">Messages last session: ' + data["recentSessionMessages"].toLocaleString("en-US") + '</span></p>');
            $('#messagesStatusBar').append('<p class="status-bar-field"><span class="status-bar-right">Total messages: ' + data["totalMessages"].toLocaleString("en-US") + '</span></p>');
        }
        hide("messagesLoad");


        $('#sessionsWindowBody').append('<div class="list-group-header">Recent Sessions</div>');
        $('#sessionsWindowBody').append('<div class="action-group" id="sessionsActionGroup"><button class="action-button" id="sessionsExpandButton">Expand all</button><button class="action-button" id="sessionsCollapseButton">Collapse all</button></div>');
        $('#sessionsWindowBody').append('<ul id="recentSessionsList">');
        var currentSessionId = data["recentSegmentSessions"][0];
        var segmentCount = 0;
        var numSegmentsThisSession = 1;
        for(let i = 0; i < data["recentSessionStartDatetimes"].length; i++)
        {
            var sessionStartDatetime = data["recentSessionStartDatetimes"][i].split(' ');
            sessionStartDatetime = new Date(sessionStartDatetime[0] + "T" + sessionStartDatetime[1] + "Z");
            sessionStartDatetime = milToDatetime(sessionStartDatetime);
            var sessionLength = data["recentSessionLengths"][i];
            if(sessionLength == "null")
            {
                sessionLength = "LIVE";
                $('#recentSessionsList').append('<li class="session-item"><i class="fas fa-calendar-days prefix-icon";"></i><span class="session-start-date">' + sessionStartDatetime["date"] + '</span><i class="fas fa-clock prefix-icon"></i><span class="session-start-time">' + sessionStartDatetime["time"] + '</span><div class="live prefix-icon"><div class="circle pulse live-length"></div></div><span class="session-length live-length">' + sessionLength + '</span><div class="selector session-selector" id="' + channel + '-session-' + (i+1) + '"></div></li>');
            }
            else
            {
                sessionLength = lengthToTime(sessionLength);
                $('#recentSessionsList').append('<li class="session-item"><i class="fas fa-calendar-days prefix-icon";"></i><span class="session-start-date">' + sessionStartDatetime["date"] + '</span><i class="fas fa-clock prefix-icon"></i><span class="session-start-time">' + sessionStartDatetime["time"] + '</span><i class="fas fa-timer prefix-icon"></i><span class="session-length">' + sessionLength + '</span><div class="selector session-selector" id="' + channel + '-session-' + (i+1) + '"></div></li>');
            }
            var sessionId = data["recentSegmentSessions"][segmentCount];
            $('#recentSessionsList').append('<div class="session-info" id="' + channel + '-session-' + (i+1) + '-info" style="display:none;">');
            while(sessionId == currentSessionId)
            {
                if(numSegmentsThisSession == 1)
                {
                    $('#' + channel + '-session-' + (i+1) + '-info').append('<li><span class="stream-title">' + data["recentSegmentTitles"][segmentCount] + '</span></li>');
                }
                var segmentLength = data["recentSegmentLengths"][segmentCount];
                if(segmentLength.length == 0)
                {
                    segmentLength = 'LIVE';
                    $('#' + channel + '-session-' + (i+1) + '-info').append('<li class="segment-info"><span class="category-name">' + data["recentSegmentCategories"][segmentCount] + '</span><span class="segment-length"><div class="live"><div class="circle pulse live-length"></div></div><span class="segmentLengthText live-length">' + segmentLength + '</span></span></li>');
                }
                else
                {
                    segmentLength = lengthToTime(segmentLength);
                    $('#' + channel + '-session-' + (i+1) + '-info').append('<li class="segment-info"><span class="category-name">' + data["recentSegmentCategories"][segmentCount] + '</span><span class="segment-length"><i class="fas fa-timer"></i><span class="segmentLengthText">' + segmentLength + '</span></span></li>');
                }
                segmentCount += 1;
                numSegmentsThisSession += 1;
                sessionId = data["recentSegmentSessions"][segmentCount];
            }
            currentSessionId = sessionId;
            numSegmentsThisSession = 1;
            $('#sessionsWindowBody').append('<div class="session-info">')

        }
        $('#sessionsWindowBody').append('</ul>');
        hide("sessionsLoad");
        $('#' + channel + '-channelName').removeClass("mouse-down");

    }
    catch(err) {
        console.log(err);
    }
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

function showLoginPage() {
    if(state != "main") {
        remove(state);
    }
    else
    {
        hide(state);
    }
    var login_page = '<div class="window" id="login"><div class="title-bar window-blue"><div class="title-bar-text"><i class="fas fa-user"></i>Chattercat - Log in</div></div><div class="window-body" id="loginWindowBody"><label for="uname"><span class="login-text">Username:</span></label><input id="username" type="text" placeholder="Enter Username" name="uname" autocomplete="off" required><p><label for="psw"><span class="login-text">Password:</span></label><input id="password" type="password" placeholder="Enter Password" name="psw" autocomplete="off" required><button type="submit" id="loginButton">Login</button></div><span class="bad-login" id="badLoginText">Invalid login. Please try again.</span></div>';
    $('body').append(login_page);
    state = "login";
}

function hide(id) {
    $('#' + id).css("display", "none");
}

function show(id) {
    $('#' + id).css("display", "block");
}

function remove(id) {
    document.getElementById(id).remove();
}

function generateChannelPage(channel)
{
    state = "statsPage";
    document.body.innerHTML += '<div class="window-group" id="statsPage"><div class="window window-group-member"><div class="title-bar"><div class="title-bar-text" id="chattersTitleBarText"><i class="fas fa-cat-space"></i></div></div><div class="window-body" id="chattersWindowBody"><div class="load" id="chattersLoad"><span class="loader"></span></div></div><div class="status-bar" id="chattersStatusBar"></div></div><div class="window window-group-member"><div class="title-bar member-2"><div class="title-bar-text" id="emotesTitleBarText"><i class="fas fa-cat-space"></i></div></div><div class="window-body" id="emotesWindowBody"><div class="load" id="emotesLoad"><span class="loader"></span></div></div><div class="status-bar" id="emotesStatusBar"></div></div><div class="window window-group-member"><div class="title-bar member-3"><div class="title-bar-text" id="messagesTitleBarText"><i class="fas fa-cat-space"></i></div></div><div class="window-body" id="messagesWindowBody"><div class="load"><span class="loader" id="messagesLoad"></span></div></div><div class="status-bar" id="messagesStatusBar"></div></div><div class="window window-group-member"><div class="title-bar member-4"><div class="title-bar-text" id="sessionsTitleBarText"><i class="fas fa-cat-space"></i></div></div><div class="window-body" id="sessionsWindowBody"><div class="load" id="sessionsLoad"><span class="loader"></span></div></div></div><div class="window-group"><div class="window-group-member" id="updates"><div class="window" id="updatesPanel"><div class="title-bar"><div class="title-bar-text"><i class="fas fa-cat-space"></i>' + channel + ' - Emote Update Log</div></div><div class="window-body"><ul class="emote-log"></ul></div></div></div></div></div>';
}

// 
// Utility Functions
// 

// mil = military time
function milToTime(mil)
{
    var hours = mil.getHours();
    var minutes = mil.getMinutes();
    var seconds = mil.getSeconds();
    var meridiem = '';
    var ret = '';
    if(hours > 12)
    {
        ret += hours-12 + ':';
        meridiem = 'PM';
    }
    else
    {
        if(hours == 0)
        {
            hours += 12;
        }
        ret+= hours + ':';
        meridiem = 'AM';
    }
    if(minutes < 10)
    {
        ret += '0' + minutes;
    }
    else
    {
        ret += minutes;
    }
    // if(seconds < 10)
    // {
    //     ret += '0' + seconds + '';
    // }
    // else
    // {
    //     ret += seconds + '';
    // }
    ret += meridiem;
    return ret;
}

function milToDatetime(mil)
{
    var year = mil.getFullYear().toString().substring(2,4);
    var month = mil.getMonth()+1;
    var day = mil.getDate();
    var hours = mil.getHours();
    var minutes = mil.getMinutes();
    var seconds = mil.getSeconds();
    var meridiem = '';
    var ret = [];
    ret["date"] = month + '/' + day + '/' + year;
    ret["time"] = '';
    if(hours >= 12)
    {
        if(hours > 12)
        {
            ret["time"] += hours-12 + ':';
        }
        else
        {
            ret["time"] += hours + ':';
        }
        meridiem = 'PM';
    }
    else
    {
        if(hours == 0)
        {
            hours += 12;
        }
        ret["time"] += hours + ':';
        meridiem = 'AM';
    }
    if(minutes < 10)
    {
        ret["time"] += '0' + minutes + ':';
    }
    else
    {
        ret["time"] += minutes + ':';
    }
    if(seconds < 10)
    {
        ret["time"] += '0' + seconds + '';
    }
    else
    {
        ret["time"] += seconds + '';
    }
    ret["time"] += meridiem;
    return ret;
}

function msToTime(ms)
{
    var days = 0;
    var hours = 0;
    var minutes = 0;
    var ret = '';
    while(ms > 0)
    {
        while(ms >= 86400000)
        {
            days += 1;
            ms -= 86400000;
        }
        while(ms >= 3600000)
        {
            hours += 1;
            ms -= 3600000;
        }
        while(ms >= 60000)
        {
            minutes += 1;
            ms -= 60000;
        }
        if(days > 0)
        {
            ret += days + 'd ';
        }
        if(hours > 0)
        {
            ret += hours + 'h ';
        }
        ret += minutes + 'm';
        return ret;
    }
}

function lengthToTime(length)
{
    var ret = '';
    var time = length.split(':');
    var hours = parseInt(time[0]);
    var minutes = parseInt(time[1]);
    var seconds = parseInt(time[2]);
    var days = 0;
    if(hours >= 24)
    {
        while(hours >= 24)
        {
            days += 1;
            hours -= 24;
        }
    }
    if(days > 0)
    {
        ret += days + 'd ';
    }
    if(hours > 0)
    {
        ret += hours + 'h ';
    }
    if(minutes > 0)
    {
        if(seconds >= 30)
        {
            minutes += 1;
        }
        ret += minutes + 'm';
    }
    else
    {
        ret += seconds + 's';
    }
    return ret;
}
