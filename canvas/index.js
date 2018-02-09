'use strict';

const connector = require('./assets/js/connect');

function login(e) {
  console.error('login e: ', e);

  let msg = '';
  let color = 'admin';
  let id = document.getElementById('userId').value;
  let pw = document.getElementById('password').value;
  let loginMsg = document.getElementById('loginMsg');
  let login = document.getElementById('login');
  let dockWrapper = document.getElementById('dockWrapper');

  // Ignore unless user pressed enter in pwd field OR clicked submit button
  if (e.type === 'keypress' && e.charCode === 13 || e.type === 'click') {
    if(id === ''){
      msg = 'Please enter your ID';
    } else if (pw === '') {
      msg = 'Please enter your password';
    // TODO Handle real auth
    } else if (id === 'test' && pw === 'test123') {
      // Authenticated
      login.classList.remove('fadeIn');
      login.classList.add('fadeOut');
      setTimeout( function() {
        login.parentElement.removeChild(login);
      }, 300);
      dockWrapper.style.display = 'flex';
      msg = 'Welcome';
      color = 'viewer';
    } else {
      msg = 'ID and/or Password Incorrect';
    }
  }

  loginMsg.innerHTML = msg;
  loginMsg.classList = ''; // Clear out old color
  loginMsg.classList.add(color);


}

function showOptions(target) {
  return target.lastElementChild.style.visibility = "visible";
}
function hideOptions(target) {
  return target.lastElementChild.style.visibility = "hidden";
}

function openApp(name, role, port) {
  connector.tryTunnel("derp")
  let roleIcon = '';
  if(role === 'viewer') {
    roleIcon = 'far fa-eye';
  } else if (role === 'editor') {
    roleIcon = 'far fa-file-edit';
  } else { // admin
    roleIcon = 'fab fa-black-tie';
  }
  let view = document.createElement('div');
  view.id = name + '_' + role;
  view.classList.add('app');
  // view.draggable = 'true';
  // view.setAttribute("ondrag", "drag(event)");
  view.innerHTML = `
    <div class="wrapper ` + role + `-bg" onclick="bringToFront('` + view.id + `')">
      <div
        class="win-bar"
        ondragstart="dragstart(event)"
        ondrag="drag(event)"
        ondragend="dragend(event)"
        draggable="true"
      >
        <div style="margin-left: -10px;">
          <i class="` + roleIcon + ` fa-2x"></i>
        </div>
        <div style="flex: 1; padding-left: 10px;">` + name.charAt(0).toUpperCase() + name.slice(1,) + `</div>
        <div style="margin-right: -10px;">
          <i class="far fa-minus win-ctrl"
            onclick="minimizeApp(this);"
            title="Minimize"
          ></i>
          <i class="far fa-square win-ctrl"
            onclick="toggleMaximizeApp(this);"
            title="Toggle Fullscreen"
          ></i>
          <i class="fas fa-times win-ctrl win-close"
            onclick="closeApp(this);"
            title="Close"
          ></i>
        </div>
      </div>
      <webview src="http://localhost:` + port + `/" allowtransparency></webview>
    </div>
  `;

  document.body.appendChild(view);
}

function toggleMaximizeApp(target) {
  let app = target.parentElement.parentElement.parentElement.parentElement;
  if(app.style.width === '100%' && app.style.height === '100%') {
    // get rid of maximize icon
    target.classList.remove('fa-clone');
    // replace with minimize icon
    target.classList.add('fa-square');
    // set style values
    app.style.left = '25%';
    app.style.top = '25%';
    app.style.width = '50%';
    return app.style.height = '50%'
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
  let app = target.parentElement.parentElement.parentElement.parentElement;
  return app.parentElement.removeChild(app);
}
function toggleMinimizedDrawer(role) {
  console.warn('toggleMinimizedDrawer role: ', role);
  // Open and Close minimized app drawer
  let drawer = document.getElementById('minimized_' + role);
  let count = document.getElementById('minimized_' + role + '_count');
  let close = document.getElementById('minimized_' + role + '_close');
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
let counts = {
  admin: 0,
  editor: 0,
  viewer: 0
}

function minimizeApp(target) {
  let app = target.parentElement.parentElement.parentElement.parentElement;
  console.warn('app: ', app);
  // Get App Name and Role
  let info = app.id.split('_');
  console.warn('info: ', info);
  let name = info[0];
  let role = info[1];
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

  setTimeout( function() {
    // show the minimized apps drawer
    let drawer = document.getElementById('minimized_' + role + '_drawer');
    drawer.style.display = 'flex';

    app.style.display = "none";
    let wrapper = document.createElement('div');
    wrapper.classList.add('min-mark-wrapper');
    wrapper.setAttribute("onclick", "unminimizeApp(this, '" + app.id + "')");
    let node = document.createElement('I');
    node.classList.add(iconType, iconGlyph, 'min-mark', role);
    wrapper.appendChild(node);
    let elId = 'minimized_' + role;
    document.getElementById(elId).appendChild(wrapper);
  }, 300);

  // Update counts
  counts[role] += 1;
  document.getElementById('minimized_' + role + '_count').innerText = counts[role];

}

function unminimizeApp(target, appID) {
  // remove the minimized app marker from the dock
  target.parentElement.removeChild(target);
  // Get the app element
  let app = document.getElementById(appID);
  // Slide the app back into view
  app.style.display = 'flex';
  app.classList.remove('fadeOutRight');
  app.classList.add('fadeInRight');

  // Close minimized app drawer
  let role = appID.split('_')[1];
  document.getElementById('minimized_' + role).style.display = 'none';
  // Update minimized app count
  counts[role] -= 1;
  let el = document.getElementById('minimized_' + role + '_count');
  el.innerText = counts[role];
  el.style.display = "block";
  document.getElementById('minimized_' + role + '_close').style.display = 'none';

  if (counts[role] === 0) { // There are no apps in the drawer
    // show the minimized apps drawer
    let drawer = document.getElementById('minimized_' + role + '_drawer');
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
  let win = e.target.parentElement.parentElement;
  // Bring the window being dragged to the front
  console.warn('WIN: ', win);
  bringToFront(win.id);

  // figure out offset from mouse to upper left corner
  // of element we want to drag
  let style = window.getComputedStyle(win, null);
  offsetLeft = parseInt(style.left, 10) - e.clientX;
  offsetTop = parseInt(style.top, 10) - e.clientY;
}

function drag(e) {
  // Get the app window/element
  let win = e.target.parentElement.parentElement;

  // Set element style to move to where user drags
  win.style.left = e.clientX + offsetLeft + 'px';
  win.style.top = e.clientY + offsetTop + 'px';

  // console.error('client X,Y', e.clientX, e.clientY);
  // console.error('offset X,Y', offsetLeft, offsetTop);
  // console.error('window X,Y', win.style.left, win.style.top);
}

function dragend(e) {
  // Get the app window/element
  let win = e.target.parentElement.parentElement;

  // Keep window from snapping back to original position
  // Keep the user's drag changes
  win.style.left = e.clientX + offsetLeft + 'px';
  win.style.top = e.clientY + offsetTop + 'px';
}

// Focus clicked window
function bringToFront(appId) {
  let apps = document.querySelectorAll('.app');
  apps.forEach((a) => {
    if(a.id === appId) {
      return a.style.zIndex = 1;
    } else {
      return a.style.zIndex = 0;
    }
  });
}
