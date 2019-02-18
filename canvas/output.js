'udatase strict';

const exec = require('child_process').exec;
const fs = require('fs');
const debug = require('debug')('connector');
var Client = require('ssh2').Client;
let data = null;
const express = require('express')
  , logger = require('morgan')
  , session = require('express-session');
const Grant = require('grant-express')
  , grant = new Grant(require('./config.json'));
const app = express();
app.use(logger('dev'));
app.use(session({ secret: 'grant',
  resave: true,
  saveUninitialized: true }));
app.use(grant);
var Client = require('node-rest-client').Client;
const client = new Client();

let excaliburIpAddress;


function createTunnel(options, roleName, data) {
  console.log('entry: createTunnel()');

  const createTunnelCommand = `ssh -i ${
    options.privateKey
  } ${
    options.username
  }@${
    options.host
  } -p ${
    options.port
  } -4 -L ${
    options.localPort
  }:${
    options.dstHost
  }:${
    options.dstPort
  } -N -o "StrictHostKeyChecking no" "LANG=en_US.UTF-8" `;

  console.log('create_tunnel_command = : ', createTunnelCommand);

  exec(createTunnelCommand, (error, stdout, stderr) => {
    console.log('stdout: ', stdout);
    console.log('stderr: ', stderr);
    console.log('error: ', error);
    if (error) {
      debug(`exec error: ${error}`);
      return;
    }
  });

  displayApp(roleName, options.localPort, data);

  console.log('exit: createTunnel()');
}


const connector = require('./assets/js/connect');
function showOptions(target) {
  return target.lastElementChild.style.visibility = 'visible';
}


function hideOptions(target) {
  return target.lastElementChild.style.visibility = 'hidden';
}


function stopVirtueForApp(roleId) {
  console.log('entry: stopVirtue()');

  const client = methods();
  const args = {
    headers: { Authorization: `Bearer ${data.access_token}` },
  }

  client.methods.userVirtueList(args, (virtueList, resp) => {
    const numberOfVirtues = virtueList.length

    for (let virtueIndex = 0;
      virtueIndex < numberOfVirtues;
      virtueIndex += 1) {
      if (virtueList[virtueIndex].roleId == roleId) {
        console.log(`data = ${virtueList[virtueIndex]}`);

        const virtueId = virtueList[virtueIndex].id;

        const args = {
          parameters: { virtueId },
          headers: { Authorization: `Bearer ${data.access_token}` },
        };

        client.methods.userVirtueStop(args);
      }
    }
  });
  console.log('exit: stopVirtue()');
}


function displayApp(roleName, localPort, data) {
  console.log('entry: displayApp()');

  const name = data.name;
  const view = document.createElement('div');
  const roleIcon = 'fab fa-black-tie';

  view.id = `${name}_${roleName}`;
  view.classList.add('app');
  view.draggable = true;
  view.setAttribute('ondrag', 'drag(event)');
  view.setAttribute('ondragstart', 'dragstart(event)');
  view.setAttribute('ondragend', 'dragend(event)');
  view.setAttribute('appid', `${name.charAt(0).toLowerCase()}${name.slice(1)}`);
  view.innerHTML = `${'\n    <div class="wrapper ' + 'editor' + "-bg\" onclick=\"bringToFront('"}${view.id}')">\n      <div class="win-bar">\n        <div style="margin-left: -10px;">\n          <i class="${roleIcon} fa-2x"></i>\n        </div>\n        <div style="flex: 1; padding-left: 10px;">${name.charAt(0).toUpperCase()}${name.slice(1)}</div>\n        <div style="margin-right: -10px;">\n          <i class="far fa-minus win-ctrl"\n            onclick="minimizeApp(this);"\n            title="Minimize"\n          ></i>\n          <i class="far fa-square win-ctrl"\n            onclick="toggleMaximizeApp(this);"\n            title="Toggle Fullscreen"\n          ></i>\n          <i class="fas fa-times win-ctrl win-close"\n      appId=${name}     onclick="closeApp(this);"\n            title="Close"\n          ></i>\n        </div>\n      </div>\n      <webview src="http://localhost:${localPort}/" allowtransparency></webview>\n    </div>\n  `;
  document.getElementById('appArea').appendChild(view);

  console.log('exit: displayApp()');
}


function startApp(virtueId, appId, roleName, ip, localPort) {
  console.log('entry: startApp()');

  const args = {
    parameters: { virtueId },
    headers: { Authorization: `Bearer ${data.access_token}` },
  };

  client.methods.userVirtueLaunch(args, (virtue, response) => {
    const args = {
      parameters: { appId, virtueId },
      headers: { Authorization: `Bearer ${data.access_token}` },
    };

    client.methods.userApplicationGet(args, function(app, resp) {
      const local_config = {
        username: 'virtue',
        host: ip,
        port: app.port,
        dstHost: '127.0.0.1',
        dstPort: 2023,
        localHost: '0.0.0.0',
        localPort,
        privateKey: 'key.pem',
      };

      client.methods.userApplicationLaunch(args, (app1, resp1) => {
        console.log('entry: userApplicationLaunch()');
        createTunnel(local_config, roleName, app);
      });
    });
  });

  console.log('exit: startApp()');
}


function openApp(roleName, localPort, appId, roleId) {
  console.log('entry: openApp()');

  const client = methods();
  const args = {
    headers: { Authorization: `Bearer ${data.access_token}` },
  }

  client.methods.userVirtueList(args, (virtueList, resp) => {
    const numberOfVirtues = virtueList.length;

    for (let virtueIndex = 0;
      virtueIndex < numberOfVirtues;
      virtueIndex += 1) {
      if (virtueList[virtueIndex].roleId == roleId) {
        const virtueId = virtueList[virtueIndex].id;
        const ip = virtueList[virtueIndex].ipAddress;

        startApp(virtueId, appId, roleName, ip, localPort);
      }
    }
  });

  console.log('exit: openApp()');
}


function toggleMaximizeApp(target) {
  const app = target.parentElement.parentElement.parentElement.parentElement;
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
  } else {
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
  const client = methods();
  const app = target.parentElement.parentElement.parentElement.parentElement;
  const appId = app.getAttribute('appid');
  console.log('appId = ' + appId);
  const args = {
    parameters: { appId },
    headers: { Authorization: `Bearer ${data.access_token}` },
  };

  client.methods.userApplicationStop(args);
  return app.parentElement.removeChild(app);
}


function toggleMinimizedDrawer(role) {
  console.warn('toggleMinimizedDrawer role: ', role);
  // Open and Close minimized app drawer
  const drawer = document.getElementById(`minimized_${role}`);
  const count = document.getElementById(`minimized_${role}_count`);
  const close = document.getElementById(`minimized_${role}_close`);
  if (drawer.style.display === 'none') {
    drawer.style.display = 'flex';
    count.style.display = 'none';
    close.style.display = 'block';
  } else {
    drawer.style.display = 'none';
    count.style.display = 'block';
    close.style.display = 'none';
  }
}


const counts = {
  admin: 0,
  editor: 0,
  viewer: 0,
};


function minimizeApp(target) {
  const app = target.parentElement.parentElement.parentElement.parentElement;
  console.warn('app: ', app);
  // Get App Name and Role
  const info = app.id.split('_');
  console.warn('info: ', info);
  const name = info[0];
  const role = info[1];
  let iconType = 'fas';
  let iconGlyph = 'fa-circle';
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
  setTimeout(() => {
    // show the minimized apps drawer
    const drawer = document.getElementById(`minimized_${role}_drawer`);
    drawer.style.display = 'flex';
    app.style.display = 'none';
    const wrapper = document.createElement('div');
    wrapper.classList.add('min-mark-wrapper');
    wrapper.setAttribute('onclick', `unminimizeApp(this, '${app.id}')`);
    const node = document.createElement('I');
    node.classList.add(iconType, iconGlyph, 'min-mark', role);
    wrapper.appendChild(node);
    const elId = `minimized_${role}`;
    document.getElementById(elId).appendChild(wrapper);
  }, 300);
  // Update counts
  counts[role]  +=  1;
  document.getElementById(`minimized_${role}_count`).innerText = counts[role].toString();
}


function unminimizeApp(target, appID) {
  // remove the minimized app marker from the dock
  target.parentElement.removeChild(target);
  // Get the app element
  const app = document.getElementById(appID);
  // Slide the app back into view
  app.style.display = 'flex';
  app.classList.remove('fadeOutRight');
  app.classList.add('fadeInRight');
  // Close minimized app drawer
  const role = appID.split('_')[1];
  document.getElementById(`minimized_${role}`).style.display = 'none';
  // Update minimized app count
  counts[role] -= 1;
  const el = document.getElementById(`minimized_${role}_count`);
  el.innerText = counts[role];
  el.style.display = 'block';
  document.getElementById(`minimized_${role}_close`).style.display = 'none';
  if (counts[role] === 0) {
    // show the minimized apps drawer
    const drawer = document.getElementById(`minimized_${role}_drawer`);
    drawer.style.display = 'none';
  } else {
    return;
  }
}


// Drag and Drop
let offsetLeft = 0;
let offsetTop = 0;
function dragstart(e) {
  // Get the app window/element
  const win = e.target;
  // Bring window to front
  bringToFront(win.id);
  // figure out offset from mouse to upper left corner
  // of element we want to drag
  const style = window.getComputedStyle(win, null);
  const l = Number(style.left.slice(0, style.left.length - 2));
  const t = Number(style.top.slice(0, style.top.length - 2));
  offsetLeft = l - e.clientX;
  offsetTop = t - e.clientY;
}


function drag(e) {
  const win = e.target;
  // Hide the non-dragging element
  win.style.visibility = 'hidden';
}


function dragend(e) {
  const win = e.target;
  // Make the app visible again
  win.style.visibility = 'visible';
  // Keep window from snapping back to original position
  // and keep the user's drag changes
  const left = e.clientX + offsetLeft;
  const top = e.clientY + offsetTop;
  win.style.left = left.toString().concat('px');
  win.style.top = top.toString().concat('px');
}


// Focus clicked window
function bringToFront(appId) {
  // Must convert NodeList to Array
  const appList = document.querySelectorAll('.app'), apps = [].slice.call(appList);
  apps.map((a) => {
    if (a.id === appId) {
      return a.style.zIndex = 1;
    } else {
      return a.style.zIndex = 0;
    }
  });
}


function login(e) {
  console.log('login() entry');

  excaliburIpAddress = 'excalibur.galahad.com';
  checkOAuth();

  console.log('login() exit');
}


function executeExcaliburCallback(request, response, iframe) {
  console.log('entry: executeExcaliburCallback()');
  console.log(`query: ${request.query}`);

  const dockWrapper = document.getElementById('dockWrapper');
  const login = document.getElementById('login');

  iframe.parentElement.removeChild(iframe);
  response.end(JSON.stringify(request.query, null, 2));

  if (request.query.hasOwnProperty('access_token')) {
    console.log('access_token found');

    //login.classList.remove('fadeIn');
    //login.classList.add('fadeOut');
    dockWrapper.style.display = 'flex';
    data = request.query;
    createVirtueDock();

    console.log('exit retrieve');
  } else {
    console.log('error - error_description');
  }

  console.log('exit: executeExcaliburCallback()');
}


function checkOAuth() {
  // Needed for self-signed cert
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

  const login = document.getElementById('login');
  const iframe = document.createElement('iframe');

  //window.open("http://canvas.com:3000/connect/excalibur")
  iframe.setAttribute('src', 'http://canvas.com:3000/connect/excalibur');
  iframe.style.background = 'white';
  iframe.setAttribute('width', '100%');
  iframe.setAttribute('height', '100%');

  app.get('/excalibur_callback', (req, res) => {
    executeExcaliburCallback(req, res, iframe)
});

  app.listen(3000, () => {
    console.log(`Express server listening on port ${3000}`);
  });

  login.parentElement.appendChild(iframe);
  login.parentElement.removeChild(login);
}


function populateApps(roleList, roleIndex, numberOfApps) {
  console.log('entry: populateApps()');

  for (let appIndex = 0;
    appIndex < numberOfApps;
    appIndex += 1) {
    const appId = roleList[roleIndex].applicationIds[appIndex];
    const localPort = `1${roleIndex}${appIndex}00`;
    
    // Updates app dock
    const div = document.createElement('div');
    const optionsinner = document.getElementById(`optionsinner${roleIndex}`);
    optionsinner.setAttribute('name', roleList[roleIndex].id);
    
    div.setAttribute('class', 'icon-pair circle-bg');
    if (roleList[roleIndex].ipAddress !== 'null') {
      div.setAttribute(
        'onclick',
        //`openApp(
        //  '${roleList[roleIndex].name}',
        //  '${localPort}',
        //  '${appId}',
        //  '${roleList[roleIndex].id}
        //  ');`,
        `openApp('${
            roleList[roleIndex].name
            }','${
            localPort
            }','${
            appId
            }','${
            roleList[roleIndex].id
            }');`,
      );
    }

    const itag = document.createElement('I');
    itag.setAttribute('class', 'far fa-file-edit fa-2x');
    div.appendChild(itag);
    optionsinner.appendChild(div);
  }

  console.log('exit: populateApps()');
}


function addVirtuesToSideDock(roleList) {
  console.log('entry: addVirtuesToSideDock()');

  const dockWrapper = document.getElementById('dockWrapper');
  const numberOfRoles = roleList.length;

  dockWrapper.style.display = 'flex';

  for (let roleIndex = 0;
    roleIndex < numberOfRoles;
    roleIndex += 1) {
    const option = document.getElementById(`options${roleIndex}`);
    const name = document.getElementById(`dock${roleIndex}`);
    const numberOfApps = roleList[roleIndex].applicationIds.length;

    name.innerHTML = roleList[roleIndex].name;
    option.style.display = 'flex';

    populateApps(roleList, roleIndex, numberOfApps);
  }

  console.log('exit: addVirtuesToSideDock()');
}


function addStopButtonToVirtues(virtueList) {
  console.log('entry: addStopButtonToVirtues()');

  const numberOfVirtues = virtueList.length;
      
  for (let virtueIndex = 0;
    virtueIndex < numberOfVirtues;
    virtueIndex += 1) {
    const roleId = virtueList[virtueIndex].roleId;
    const optionsinner = document.getElementsByName(roleId)[0];
    const stop_app = document.createElement('input');
    console.log(`optionsinner = ${optionsinner}`);
      
    stop_app.setAttribute('class', 'control_button');
    stop_app.setAttribute('type', 'control_button');
    stop_app.setAttribute('value', 'STOP');
    stop_app.setAttribute(
      'onclick',
      `stopVirtueForApp('${
        virtueList[virtueIndex].roleId
      }');`,
    );
      
    optionsinner.appendChild(stop_app);
  }

  console.log('exit: addStopButtonToVirtues()');
}


function createVirtueDock() {
  console.log('entry: createVirtueDock()');

  const client = methods();
  const args = {
    headers: { Authorization: `Bearer ${data.access_token}` },
  };

  client.methods.userRoleList(args, (roleList, resp) => {
    addVirtuesToSideDock(roleList);

    client.methods.userVirtueList(args, function (virtueList, resp) {
      //addStopButtonToVirtues(virtueList);
    });
  });
  console.log('exit: createVirtueDock()');
}


function logout(e) {
  const gui = require('nw.gui');
  gui.App.quit();
}


function methods() {
  console.log('entry: methods()');

  const excalibur = `https://${excaliburIpAddress}:5002/virtue`;

  client.registerMethod(
    'logout',
    `https://${excaliburIpAddress}:5002/oauth2/revoke`,
    'POST',
  );

  client.registerMethod(
    'userRoleGet',
    `${excalibur}/user/role/get`,
    'GET',
  );

  client.registerMethod(
    'userRoleList',
    `${excalibur}/user/role/list`,
    'GET',
  );

  client.registerMethod(
    'userApplicationGet',
    `${excalibur}/user/application/get`,
    'GET',
  );

  client.registerMethod(
    'userApplicationLaunch',
    `${excalibur}/user/virtue/application/launch`,
    'GET',
  );

  client.registerMethod(
    'userApplicationStop',
    `${excalibur}/user/virtue/application/stop`,
    'GET',
  );

  client.registerMethod(
    'userVirtueGet',
    `${excalibur}/user/virtue/get`,
    'GET',
  );

  client.registerMethod(
    'userVirtueList',
    `${excalibur}/user/virtue/list`,
    'GET',
  );

  client.registerMethod(
    'userVirtueLaunch',
    `${excalibur}/user/virtue/launch`,
    'GET',
  );

  client.registerMethod(
    'userVirtueStop',
    `${excalibur}/user/virtue/stop`,
    'GET',
  );

  console.log('exit: methods()');

  return client;
}
