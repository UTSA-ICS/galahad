'use strict';

// SSH -L
const connector = require('./assets/js/connect');

function showOptions(target: any) {
  return target.lastElementChild.style.visibility = "visible";
}
function hideOptions(target: any) {
  return target.lastElementChild.style.visibility = "hidden";
}

function openApp(name: string, role: string, port: string) {
  
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
  view.draggable = true;
  view.setAttribute("ondrag", "drag(event)");
  view.setAttribute("ondragstart", "dragstart(event)");
  view.setAttribute("ondragend", "dragend(event)");
  view.innerHTML = `
    <div class="wrapper ` + role + `-bg" onclick="bringToFront('` + view.id + `')">
      <div class="win-bar">
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

  document.getElementById('appArea').appendChild(view);
}

function toggleMaximizeApp(target: any) {
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
function closeApp(target: any) {
  let app = target.parentElement.parentElement.parentElement.parentElement;
  return app.parentElement.removeChild(app);
}
function toggleMinimizedDrawer(role: string) {
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

interface Counts {
  admin: number;
  editor: number;
  viewer: number;
  [key: string]: number;
}
let counts: Counts = {
  admin: 0 as number,
  editor: 0 as number,
  viewer: 0 as number
}

function minimizeApp(target: any) {
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
  document.getElementById('minimized_' + role + '_count').innerText = counts[role].toString();
}

function unminimizeApp(target: any, appID: string) {
  // remove the minimized app marker from the dock
  target.parentElement.removeChild(target);
  // Get the app element
  let app: any = document.getElementById(appID);
  // Slide the app back into view
  app.style.display = 'flex';
  app.classList.remove('fadeOutRight');
  app.classList.add('fadeInRight');

  // Close minimized app drawer
  let role: string = appID.split('_')[1];
  document.getElementById('minimized_' + role).style.display = 'none';
  // Update minimized app count
  counts[role] -= 1;
  let el: any = document.getElementById('minimized_' + role + '_count');
  el.innerText = counts[role];
  el.style.display = "block";
  document.getElementById('minimized_' + role + '_close').style.display = 'none';

  if (counts[role] === 0) { // There are no apps in the drawer
    // show the minimized apps drawer
    let drawer: any = document.getElementById('minimized_' + role + '_drawer');
    drawer.style.display = 'none';
  } else {
    return;
  }
}

// Drag and Drop
let offsetLeft: number = 0;
let offsetTop: number = 0;

function dragstart(e: any) {
  // Get the app window/element
  let win: HTMLDivElement = e.target;

  // Bring window to front
  bringToFront(win.id);

  // figure out offset from mouse to upper left corner
  // of element we want to drag
  let style: any = window.getComputedStyle(win, null);
  let l: number = Number(style.left.slice(0, style.left.length - 2));
  let t: number = Number(style.top.slice(0, style.top.length - 2));
  offsetLeft = l - e.clientX;
  offsetTop = t - e.clientY;
}

function drag(e: any) {

  let win: HTMLDivElement = e.target;

  // Hide the non-dragging element
  win.style.visibility = "hidden";
}

function dragend(e: any) {

  let win: HTMLDivElement = e.target;

  // Make the app visible again
  win.style.visibility = "visible";

  // Keep window from snapping back to original position
  // and keep the user's drag changes
  let left: number = e.clientX + offsetLeft;
  let top: number = e.clientY + offsetTop;
  win.style.left =  left.toString().concat('px');
  win.style.top =  top.toString().concat('px');
}

// Focus clicked window
function bringToFront(appId: string) {
  // Must convert NodeList to Array
  const appList: any  = document.querySelectorAll('.app'),
        apps = [].slice.call(appList);

  apps.map((a: any) => {
    if(a.id === appId) {
      return a.style.zIndex = 1;
    } else {
      return a.style.zIndex = 0;
    }
  });
}
