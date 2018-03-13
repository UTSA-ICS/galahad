'use strict';
var exec = require('child_process').exec;
var fs = require('fs');
var debug = require('debug')('connector');
var Client = require('ssh2').Client;
var config = {
    username: "ubuntu",
    //password:"derp",
    host: "ec2-54-91-72-220.compute-1.amazonaws.com",
    port: 22,
    dstHost: "127.0.0.1",
    dstPort: 2023,
    localHost: "0.0.0.0",
    localPort: 2000,
    //privateKey:fs.readFileSync('key.pem')
    privateKey: "key.pem"
};
function execTunnel(options) {
    var str = "ssh -i " + config.privateKey + " " + config.username + "@" + config.host + " -p " + config.port + " -4 -L " + config.localPort + ":" + config.dstHost + ":" + config.dstPort + " -N -o \"StrictHostKeyChecking no\" ";
    console.warn('execTunnel str: ', str);
    debug('trying to connect with: ', str);
    exec(str, function (error, stdout, stderr) {
        console.warn('stdout: ', stdout);
        console.warn('stderr: ', stderr);
        console.warn('error: ', error);
        if (error) {
            debug("exec error: " + error);
            return;
        }
        debug("stdout: " + stdout);
        debug("stderr: " + stderr);
    });
}
// Connect to AWS Xpra
execTunnel("derp");
// SSH -L
var connector = require('./assets/js/connect');
function showOptions(target) {
    return target.lastElementChild.style.visibility = "visible";
}
function hideOptions(target) {
    return target.lastElementChild.style.visibility = "hidden";
}
function openApp(name, role, port) {
    var roleIcon = '';
    if (role === 'viewer') {
        roleIcon = 'far fa-eye';
    }
    else if (role === 'editor') {
        roleIcon = 'far fa-file-edit';
    }
    else {
        roleIcon = 'fab fa-black-tie';
    }
    var view = document.createElement('div');
    view.id = name + '_' + role;
    view.classList.add('app');
    view.draggable = true;
    view.setAttribute("ondrag", "drag(event)");
    view.setAttribute("ondragstart", "dragstart(event)");
    view.setAttribute("ondragend", "dragend(event)");
    view.innerHTML = "\n    <div class=\"wrapper " + role + "-bg\" onclick=\"bringToFront('" + view.id + "')\">\n      <div class=\"win-bar\">\n        <div style=\"margin-left: -10px;\">\n          <i class=\"" + roleIcon + " fa-2x\"></i>\n        </div>\n        <div style=\"flex: 1; padding-left: 10px;\">" + name.charAt(0).toUpperCase() + name.slice(1) + "</div>\n        <div style=\"margin-right: -10px;\">\n          <i class=\"far fa-minus win-ctrl\"\n            onclick=\"minimizeApp(this);\"\n            title=\"Minimize\"\n          ></i>\n          <i class=\"far fa-square win-ctrl\"\n            onclick=\"toggleMaximizeApp(this);\"\n            title=\"Toggle Fullscreen\"\n          ></i>\n          <i class=\"fas fa-times win-ctrl win-close\"\n            onclick=\"closeApp(this);\"\n            title=\"Close\"\n          ></i>\n        </div>\n      </div>\n      <webview src=\"http://localhost:" + port + "/\" allowtransparency></webview>\n    </div>\n  ";
    document.getElementById('appArea').appendChild(view);
}
function toggleMaximizeApp(target) {
    var app = target.parentElement.parentElement.parentElement.parentElement;
    if (app.style.width === '100%' && app.style.height === '100%') {
        // get rid of maximize icon
        target.classList.remove('fa-clone');
        // replace with minimize icon
        target.classList.add('fa-square');
        // set style values
        app.style.left = '25%';
        app.style.top = '25%';
        app.style.width = '50%';
        return app.style.height = '50%';
    }
    else {
        // get rid of maximize icon
        target.classList.remove('fa-square');
        // replace with minimize icon
        target.classList.add('fa-clone');
        // set style values
        app.style.left = '0';
        app.style.top = '0';
        app.style.width = '100%';
        return app.style.height = '100%';
    }
}
function closeApp(target) {
    var app = target.parentElement.parentElement.parentElement.parentElement;
    return app.parentElement.removeChild(app);
}
function toggleMinimizedDrawer(role) {
    console.warn('toggleMinimizedDrawer role: ', role);
    // Open and Close minimized app drawer
    var drawer = document.getElementById('minimized_' + role);
    var count = document.getElementById('minimized_' + role + '_count');
    var close = document.getElementById('minimized_' + role + '_close');
    if (drawer.style.display === 'none') {
        drawer.style.display = 'flex';
        count.style.display = 'none';
        close.style.display = 'block';
    }
    else {
        drawer.style.display = 'none';
        count.style.display = 'block';
        close.style.display = 'none';
    }
}
var counts = {
    admin: 0,
    editor: 0,
    viewer: 0
};
function minimizeApp(target) {
    var app = target.parentElement.parentElement.parentElement.parentElement;
    console.warn('app: ', app);
    // Get App Name and Role
    var info = app.id.split('_');
    console.warn('info: ', info);
    var name = info[0];
    var role = info[1];
    var iconType = 'fas';
    var iconGlyph = 'fa-circle';
    // Assign app icons
    switch (name) {
        case 'firefox':
            iconType = 'fab';
            iconGlyph = 'fa-firefox';
            break;
        case 'notepad':
            iconType = 'far';
            iconGlyph = 'fa-file-edit';
            break;
        case 'word':
            iconType = 'fas';
            iconGlyph = 'fa-file-word';
            break;
        default:
            iconType = 'fas';
            iconGlyph = 'fa-question-circle';
    }
    app.classList.add('fadeOutRight', 'animated');
    setTimeout(function () {
        // show the minimized apps drawer
        var drawer = document.getElementById('minimized_' + role + '_drawer');
        drawer.style.display = 'flex';
        app.style.display = "none";
        var wrapper = document.createElement('div');
        wrapper.classList.add('min-mark-wrapper');
        wrapper.setAttribute("onclick", "unminimizeApp(this, '" + app.id + "')");
        var node = document.createElement('I');
        node.classList.add(iconType, iconGlyph, 'min-mark', role);
        wrapper.appendChild(node);
        var elId = 'minimized_' + role;
        document.getElementById(elId).appendChild(wrapper);
    }, 300);
    // Update counts
    counts[role] += 1;
    document.getElementById('minimized_' + role + '_count').innerText = counts[role].toString();
}
function unminimizeApp(target, appID) {
    // remove the minimized app marker from the dock
    target.parentElement.removeChild(target);
    // Get the app element
    var app = document.getElementById(appID);
    // Slide the app back into view
    app.style.display = 'flex';
    app.classList.remove('fadeOutRight');
    app.classList.add('fadeInRight');
    // Close minimized app drawer
    var role = appID.split('_')[1];
    document.getElementById('minimized_' + role).style.display = 'none';
    // Update minimized app count
    counts[role] -= 1;
    var el = document.getElementById('minimized_' + role + '_count');
    el.innerText = counts[role];
    el.style.display = "block";
    document.getElementById('minimized_' + role + '_close').style.display = 'none';
    if (counts[role] === 0) {
        // show the minimized apps drawer
        var drawer = document.getElementById('minimized_' + role + '_drawer');
        drawer.style.display = 'none';
    }
    else {
        return;
    }
}
// Drag and Drop
var offsetLeft = 0;
var offsetTop = 0;
function dragstart(e) {
    // Get the app window/element
    var win = e.target;
    // Bring window to front
    bringToFront(win.id);
    // figure out offset from mouse to upper left corner
    // of element we want to drag
    var style = window.getComputedStyle(win, null);
    var l = Number(style.left.slice(0, style.left.length - 2));
    var t = Number(style.top.slice(0, style.top.length - 2));
    offsetLeft = l - e.clientX;
    offsetTop = t - e.clientY;
}
function drag(e) {
    var win = e.target;
    // Hide the non-dragging element
    win.style.visibility = "hidden";
}
function dragend(e) {
    var win = e.target;
    // Make the app visible again
    win.style.visibility = "visible";
    // Keep window from snapping back to original position
    // and keep the user's drag changes
    var left = e.clientX + offsetLeft;
    var top = e.clientY + offsetTop;
    win.style.left = left.toString().concat('px');
    win.style.top = top.toString().concat('px');
}
// Focus clicked window
function bringToFront(appId) {
    // Must convert NodeList to Array
    var appList = document.querySelectorAll('.app'), apps = [].slice.call(appList);
    apps.map(function (a) {
        if (a.id === appId) {
            return a.style.zIndex = 1;
        }
        else {
            return a.style.zIndex = 0;
        }
    });
}
function login(e) {
    var msg = '';
    var color = 'admin';
    var id = document.getElementById('userId').value;
    var pw = document.getElementById('password').value;
    var loginMsg = document.getElementById('loginMsg');
    var login = document.getElementById('login');
    var dockWrapper = document.getElementById('dockWrapper');
    // Ignore unless user pressed enter in pwd field OR clicked submit button
    if (e.type === 'keypress' && e.charCode === 13 || e.type === 'click') {
        if (id === '') {
            msg = 'Please enter your ID';
        }
        else if (pw === '') {
            msg = 'Please enter your password';
            // TODO Handle real auth
        }
        else {
            if (id === 'test' && pw === 'test123') {
                // Authenticated
                login.classList.remove('fadeIn');
                login.classList.add('fadeOut');
                setTimeout(function () {
                    login.parentElement.removeChild(login);
                }, 300);
                dockWrapper.style.display = 'flex';
                msg = 'Welcome';
                color = 'viewer';
            }
            else {
                msg = 'ID and/or Password Incorrect';
            }
        }
    }
    loginMsg.innerHTML = msg;
    loginMsg.className = ''; // Clear out old color
    loginMsg.classList.add(color);
}
