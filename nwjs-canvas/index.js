'use strict';

function login() {
  let msg = '';
  let color = 'hi';
  let id = document.getElementById('userId').value;
  let pw = document.getElementById('password').value;
  let loginMsg = document.getElementById('loginMsg');
  let login = document.getElementById('login');
  let dockWrapper = document.getElementById('dockWrapper');

  if(id === ''){
    msg = 'Please enter your ID';
  } else if (pw === '') {
    msg = 'Please enter your password';
  } else if (id === 'test' && pw === 'test123') {
    login.classList.remove('fadeIn');
    login.classList.add('fadeOut');
    setTimeout( function() {
      login.parentElement.removeChild(login);
    }, 300);
    dockWrapper.style.display = 'flex';
    msg = 'Welcome';
    color = 'low';
  } else {
    msg = 'ID and/or Password Incorrect';
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

function openApp(name, danger, port) {
  let dangerIcon = '';
  if(danger === 'low') {
    dangerIcon = 'fas fa-shield-check';
  } else if (danger === 'med') {
    dangerIcon = 'fas fa-question-circle';
  } else { // hi
    dangerIcon = 'fas fa-exclamation-triangle';
  }
  let view = document.createElement('div');
  view.id = name + '_' + danger;
  view.classList.add('app');
  // view.draggable = 'true';
  // view.setAttribute("ondrag", "drag(event)");
  view.innerHTML = `
    <div class="wrapper ` + danger + `-bg">
      <div
        class="win-bar"
        ondragstart="dragstart(event)"
        ondrag="drag(event)"
        ondragend="dragend(event)"
        draggable="true"
      >
        <div style="margin-left: -10px;">
          <i class="` + dangerIcon + ` fa-2x"></i>
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
function minimizeApp(target) {
  let app = target.parentElement.parentElement.parentElement.parentElement;

  // Get App Name and Danger Level
  let info = app.id.split('_');
  let name = info[0];
  let danger = info[1];
  let iconType = 'fas';
  let iconGlyph = 'fa-circle';

  // NOTE abstract into generic icon function later?
  if(danger === 'low') {
    iconType = 'fas';
    iconGlyph = 'fa-shield-check';
  } else if(danger === 'med') {
    iconType = 'fas';
    iconGlyph = 'fa-question-circle';
  } else {
    iconType = 'fas';
    iconGlyph = 'fa-exclamation-triangle';
  }

  app.classList.add('fadeOutRight', 'animated');
  setTimeout( function() {
    app.style.display = "none";
    let node = document.createElement('I');
    node.classList.add(iconType, iconGlyph, 'min-mark', danger);
    node.setAttribute("onclick", "unminimizeApp(this, '" + app.id + "')");
    document.getElementById('minimized_' + name ).appendChild(node);
  }, 300);
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
}

// Drag and Drop
let offsetLeft = 0;
let offsetTop = 0;

function dragstart(e) {
  // Get the app window/element
  let win = e.target.parentElement.parentElement;

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
